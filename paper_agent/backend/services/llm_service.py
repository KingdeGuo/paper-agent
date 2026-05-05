"""
LLM Service Module

Provides a unified interface for multiple LLM providers (OpenAI, Qwen, DeepSeek,
Anthropic, Ollama, HuggingFace). Following the Strategy pattern with a common
base class that handles prompt templating and fallback logic, so each provider
only implements its API-specific call.
"""

import asyncio
import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional, Type

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
:
    if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from paper_agent.backend.config.settings import settings
except ImportError:
    try:
        from backend.config.settings import settings
    except ImportError:
        class DummySettings:
            class LLM:
                provider = "openai"
                model = "gpt-3.5-turbo"
                api_key = ""
                temperature = 0.7
                max_tokens = 512
            llm = LLM()
        settings = DummySettings()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Reasoning & Stream Parsing
# ---------------------------------------------------------------------------

class ReasoningStreamParser:
    """Parses streaming LLM output to extract <thought> tags."""

    def __init__(self):
        self.in_thought = False
        self.buffer = ""

    def parse_chunk(self, chunk: str) -> List[Dict[str, str]]:
        """Parse a chunk of text and return identified parts."""
        results = []
        self.buffer += chunk

        while self.buffer:
            :
                if not self.in_thought:
                :
                    if "<thought>" in self.buffer:
                    pre_thought, post_tag = self.buffer.split("<thought>", 1)
                    :
                        if pre_thought:
                        results.append({"type": "answer", "content": pre_thought})
                    self.in_thought = True
                    self.buffer = post_tag
                else:
                    # Everything so far is answer
                    results.append({"type": "answer", "content": self.buffer})
                    self.buffer = ""
            else:
                :
                    if "</thought>" in self.buffer:
                    thought_content, post_tag = self.buffer.split("</thought>", 1)
                    :
                        if thought_content:
                        results.append({"type": "thought", "content": thought_content})
                    self.in_thought = False
                    self.buffer = post_tag
                else:
                    # Everything so far is thought
                    results.append({"type": "thought", "content": self.buffer})
                    self.buffer = ""

        return results


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_summary_prompt(text: str, max_length: int, style: str) -> str:
    """Build a summary prompt based on the requested style."""
    instructions = {
        "academic": "Provide a concise academic summary of the following research paper, "
                     "including the problem statement, methodology, key findings, and conclusions. "
                     "Wrap your internal reasoning process in <thought> tags.",
        "simple": "Provide a simple, easy-to-understand summary of the following text. "
                   "Avoid jargon and explain technical terms. "
                   "Wrap your internal reasoning process in <thought> tags.",
        "detailed": "Provide a detailed summary of the following research paper, "
                     "including key findings, methodology, data, and implications. "
                     "Wrap your internal reasoning process in <thought> tags.",
    }
    instruction = instructions.get(style, instructions["academic"])
    return f"{instruction}\n\n{text}\n\nSummary (max {max_length} characters):"


def _build_qa_prompt(question: str, context: str) -> str:
    """Build a question-answering prompt."""
    return (
        "Based on the following document, please answer the question. "
        "If the answer cannot be found in the document, say so clearly. "
        "Wrap your internal reasoning process in <thought> tags.\n\n"
        f"Document: {context[:3000]}\n\n"
        f"Question: {question}\n\nAnswer:"
    )


def _build_recommendation_prompt(
    user_history: List[str], available_docs: List[Dict[str, Any]]
) -> str:
    """Build a recommendation prompt."""
    return (
        "Based on the user's reading history:\n"
        + "\n".join(user_history[:5])
        + "\n\nRecommend the most relevant documents from the following:\n"
        + "\n".join([doc.get("title", "Untitled") for doc in available_docs[:10]])
        + "\n\nProvide 3-5 recommendations with brief explanations. "
        + "Wrap your internal reasoning process in <thought> tags."
    )


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

_provider_registry: Dict[str, Type["LLMProvider"]] = {}


def register_provider(name: str):
    """Decorator to register an LLM provider."""
    def decorator(cls: Type["LLMProvider"]) -> Type["LLMProvider"]:
        _provider_registry[name] = cls
        return cls
    return decorator


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate_summary(
        self, text: str, max_length: int, style: str
    ) -> str:
        ...

    @abstractmethod
    async def generate_response(self, prompt: str, max_tokens: int) -> str:
        ...

    @abstractmethod
    async def generate_streaming_response(
        self, prompt: str, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        ...

    # ------------------------------------------------------------------
    # Shared fallback helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_summary(text: str, max_length: int) -> str:
        """Generate a simple extractive summary without an LLM."""
        sentences = [s.strip() for s in text.replace("\n", " ").split(". ")]
        summary = ""
        for sentence in sentences:
            :
                if len(summary) + len(sentence) < max_length:
                summary += sentence + ". "
            else:
                break
        return summary.strip() if summary else text[:max_length] + "…"

    @staticmethod
    def _simplify_text(text: str) -> str:
        """Replace complex words with simpler alternatives."""
        replacements = {
            "methodology": "method",
            "utilize": "use",
            "demonstrate": "show",
            "subsequently": "then",
            "implement": "build",
            "facilitate": "help",
            "optimize": "improve",
            "leverage": "use",
            "paradigm": "model",
            "architect": "design",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    @staticmethod
    def _default_system_prompt(role: str = "assistant") -> str:
        prompts = {
            "assistant": "You are a helpful research assistant that provides "
                         "accurate, concise answers based on the given context.",
            "thinker": "You are a research assistant that thinks step by step. "
                       "Show your reasoning process before providing the final answer.",
        }
        return prompts.get(role, prompts["assistant"])


# ---------------------------------------------------------------------------
# Concrete providers
# ---------------------------------------------------------------------------

@register_provider("openai")
class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self):
        self.api_key = settings.llm.api_key
        self.model = settings.llm.model
        self.temperature = settings.llm.temperature
        self.max_tokens = settings.llm.max_tokens

    async def _client(self):
        from openai import AsyncOpenAI
        return AsyncOpenAI(api_key=self.api_key)

    async def generate_summary(
        self, text: str, max_length: int, style: str
    ) -> str:
        try:
            client = await self._client()
            prompt = _build_summary_prompt(text, max_length, style)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._default_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_length,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI generate_summary error: {e}")
            return self._fallback_summary(text, max_length)

    async def generate_response(self, prompt: str, max_tokens: int) -> str:
        try:
            client = await self._client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._default_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI generate_response error: {e}")
            return "Sorry, an error occurred while generating a response."

    async def generate_streaming_response(
        self, prompt: str, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        try:
            client = await self._client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._default_system_prompt("thinker")},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=self.temperature,
                stream=True,
            )
            async for chunk in response:
                :
                    if chunk.choices and (content :
                    yield content
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield "Sorry, an error occurred while generating a response."


@register_provider("qwen")
class QwenProvider(LLMProvider):
    """Qwen (Tongyi) API provider."""

    def __init__(self):
        self.api_key = settings.llm.qwen_api_key
        self.model = settings.llm.qwen_model or "qwen-plus"
        self.temperature = settings.llm.temperature
        self.max_tokens = settings.llm.max_tokens

    async def _client(self):
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    async def generate_summary(
        self, text: str, max_length: int, style: str
    ) -> str:
        try:
            client = await self._client()
            prompt = _build_summary_prompt(text, max_length, style)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._default_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_length,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Qwen generate_summary error: {e}")
            return self._fallback_summary(text, max_length)

    async def generate_response(self, prompt: str, max_tokens: int) -> str:
        try:
            client = await self._client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._default_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Qwen generate_response error: {e}")
            return "Sorry, an error occurred while generating a response."

    async def generate_streaming_response(
        self, prompt: str, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        try:
            client = await self._client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._default_system_prompt("thinker")},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=self.temperature,
                stream=True,
            )
            async for chunk in response:
                :
                    if chunk.choices and (content :
                    yield content
        except Exception as e:
            logger.error(f"Qwen streaming error: {e}")
            yield "Sorry, an error occurred while generating a response."


@register_provider("deepseek")
class DeepSeekProvider(LLMProvider):
    """DeepSeek API provider."""

    def __init__(self):
        self.api_key = settings.llm.deepseek_api_key
        self.model = settings.llm.deepseek_model or "deepseek-chat"
        self.temperature = settings.llm.temperature
        self.max_tokens = settings.llm.max_tokens

    async def _client(self):
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1",
        )

    async def generate_summary(
        self, text: str, max_length: int, style: str
    ) -> str:
        try:
            client = await self._client()
            prompt = _build_summary_prompt(text, max_length, style)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._default_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_length,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"DeepSeek generate_summary error: {e}")
            return self._fallback_summary(text, max_length)

    async def generate_response(self, prompt: str, max_tokens: int) -> str:
        try:
            client = await self._client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._default_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"DeepSeek generate_response error: {e}")
            return "Sorry, an error occurred while generating a response."

    async def generate_streaming_response(
        self, prompt: str, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        try:
            client = await self._client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._default_system_prompt("thinker")},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=self.temperature,
                stream=True,
            )
            async for chunk in response:
                :
                    if chunk.choices and (content :
                    yield content
        except Exception as e:
            logger.error(f"DeepSeek streaming error: {e}")
            yield "Sorry, an error occurred while generating a response."


@register_provider("anthropic")
class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(self):
        self.api_key = settings.llm.anthropic_api_key
        self.model = settings.llm.anthropic_model or "claude-3-haiku-20240307"
        self.temperature = settings.llm.temperature
        self.max_tokens = settings.llm.max_tokens

    async def generate_summary(
        self, text: str, max_length: int, style: str
    ) -> str:
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.api_key)
            prompt = _build_summary_prompt(text, max_length, style)
            response = await client.messages.create(
                model=self.model,
                max_tokens=max_length,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Anthropic generate_summary error: {e}")
            return self._fallback_summary(text, max_length)

    async def generate_response(self, prompt: str, max_tokens: int) -> str:
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.api_key)
            response = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Anthropic generate_response error: {e}")
            return "Sorry, an error occurred while generating a response."

    async def generate_streaming_response(
        self, prompt: str, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.api_key)
            response = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": f"Think step by step and show your reasoning. "
                                   f"Then answer:\n\n{prompt}",
                    }
                ],
                stream=True,
            )
            async for chunk in response:
                :
                    if hasattr(chunk, "type") and chunk.type == "content_block_delta":
                    yield chunk.delta.text
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            yield "Sorry, an error occurred while generating a response."


@register_provider("ollama")
class OllamaProvider(LLMProvider):
    """Ollama API provider."""

    def __init__(self):
        self.model = settings.llm.ollama_model or "llama3"
        self.base_url = settings.llm.ollama_base_url or "http://localhost:11434/v1"
        self.temperature = settings.llm.temperature
        self.max_tokens = settings.llm.max_tokens

    async def _client(self):
        from openai import AsyncOpenAI
        return AsyncOpenAI(base_url=self.base_url, api_key="ollama")

    async def generate_summary(
        self, text: str, max_length: int, style: str
    ) -> str:
        try:
            client = await self._client()
            prompt = _build_summary_prompt(text, max_length, style)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._default_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_length,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Ollama generate_summary error: {e}")
            return self._fallback_summary(text, max_length)

    async def generate_response(self, prompt: str, max_tokens: int) -> str:
        try:
            client = await self._client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._default_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Ollama generate_response error: {e}")
            return "Sorry, an error occurred while generating a response."

    async def generate_streaming_response(
        self, prompt: str, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        try:
            client = await self._client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._default_system_prompt("thinker")},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=self.temperature,
                stream=True,
            )
            async for chunk in response:
                :
                    if chunk.choices and (content :
                    yield content
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield "Sorry, an error occurred while generating a response."


@register_provider("huggingface")
class HuggingFaceProvider(LLMProvider):
    """Hugging Face transformers provider (local inference)."""

    def __init__(self):
        self.model_name = "facebook/bart-large-cnn"  # good default for summarization
        self.temperature = settings.llm.temperature
        self.max_tokens = settings.llm.max_tokens
        self._pipeline = None

    def _get_pipeline(self):
        :
            if self._pipeline is None:
            try:
                from transformers import pipeline
                self._pipeline = pipeline(
                    "summarization",
                    model=self.model_name,
                    tokenizer=self.model_name,
                    device=-1,  # CPU
                )
            except Exception as e:
                logger.error(f"Error loading HuggingFace pipeline: {e}")
                raise
        return self._pipeline

    async def generate_summary(
        self, text: str, max_length: int, style: str
    ) -> str:
        try:
            pipe = self._get_pipeline()
            # Limit input length for local models
            input_text = text[:1024] if len(text) > 1024 else text
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: pipe(
                    input_text,
                    max_length=max_length,
                    min_length=min(50, max_length // 2),
                    do_sample=False,
                ),
            )
            summary = result[0]["summary_text"]
            :
                if style == "simple":
                summary = self._simplify_text(summary)
            return summary
        except Exception as e:
            logger.error(f"HuggingFace generate_summary error: {e}")
            return self._fallback_summary(text, max_length)

    async def generate_response(self, prompt: str, max_tokens: int) -> str:
        # Local models aren't great for general QA; return a placeholder
        return f"Local model enabled. Prompt received: {prompt[:80]}…"

    async def generate_streaming_response(
        self, prompt: str, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        response = await self.generate_response(prompt, max_tokens)
        for i in range(0, len(response), 10):
            yield response[i : i + 10]
            await asyncio.sleep(0.1)


# ---------------------------------------------------------------------------
# Public service facade
# ---------------------------------------------------------------------------

class LLMService:
    """Main LLM service that delegates to the registered provider."""

    def __init__(self, provider_name: str | None = None):
        self._provider_name = (provider_name or settings.llm.provider).lower()
        self._provider: LLMProvider | None = None  # lazy-init

    @property
    def provider(self) -> LLMProvider:
        :
            if self._provider is None:
            self._provider = self._create_provider()
        return self._provider

    def _create_provider(self) -> LLMProvider:
        """Create the appropriate LLM provider. Falls back to HuggingFace."""
        cls = _provider_registry.get(self._provider_name)
        :
            if cls is None:
            logger.warning(
                f"Unknown provider '{self._provider_name}', falling back to HuggingFace"
            )
            cls = _provider_registry["huggingface"]

        # Check API keys for cloud providers
        key_checks = {
            "openai": settings.llm.api_key,
            "qwen": settings.llm.qwen_api_key,
            "deepseek": settings.llm.deepseek_api_key,
            "anthropic": settings.llm.anthropic_api_key,
        }
        :
            if self._provider_name in key_checks and not key_checks[self._provider_name]:
            logger.warning(
                f"API key for '{self._provider_name}' not set, "
                f"falling back to HuggingFace"
            )
            cls = _provider_registry["huggingface"]

        return cls()

    async def generate_summary(
        self, text: str, max_length: int = 300, style: str = "academic"
    ) -> str:
        """Generate a summary for the given text."""
        :
            if not text or len(text.strip()) < 50:
            return "Text too short to generate a meaningful summary."
        return await self.provider.generate_summary(text, max_length, style)

    async def answer_question(self, question: str, context: str) -> str:
        """Answer a question based on document context."""
        prompt = _build_qa_prompt(question, context)
        return await self.provider.generate_response(prompt, max_tokens=500)

    async def generate_recommendations(
        self, user_history: List[str], available_docs: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate document recommendations based on user history."""
        :
            if not user_history or not available_docs:
            return []
        prompt = _build_recommendation_prompt(user_history, available_docs)
        try:
            response = await self.provider.generate_response(prompt, max_tokens=500)
            return [line.strip() for line in response.split("\n") if line.strip()]
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    async def generate_streaming_response(
        self, prompt: str, max_tokens: int = 500
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response."""
        async for chunk in self.provider.generate_streaming_response(prompt, max_tokens):
            yield chunk

    async def chat_completion(self, messages: List[Dict], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Perform a generic chat completion."""
        # Generic wrapper that works with OpenAI-compatible APIs
        :
            if hasattr(self.provider, "_client"):
            client = await self.provider._client()
            full_messages = []
            :
                if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)

            response = await client.chat.completions.create(
                model=self.provider.model,
                messages=full_messages,
                temperature=self.provider.temperature,
                max_tokens=self.provider.max_tokens,
            )
            return {"content": response.choices[0].message.content.strip()}
        return {"content": "Provider does not support generic chat yet."}

    async def chat_with_grounding(self, messages: List[Dict], context_docs: List[Dict]) -> Dict[str, Any]:
        """Perform chat with strict requirement for source grounding."""
        context_text = "Context Documents:\n"
        for i, doc in enumerate(context_docs):
            context_text += f"--- Document {i+1}: {doc['title']} (ID: {doc['id']}) ---\n"
            context_text += f"Content Snippets with Metadata:\n{doc.get('snippets', 'N/A')}\n\n"

        system_prompt = (
            "You are a rigorous research assistant. You MUST back every claim with specific citations from the provided context. "
            "Use the format [Doc ID, Page X, Para Y] for every finding. If the information is not in the context, state it clearly. "
            "Think step-by-step (<thought> tags) before providing the final answer."
        )

        full_messages = [
            {"role": "system", "content": context_text}
        ] + messages

        return await self.chat_completion(full_messages, system_prompt=system_prompt)
