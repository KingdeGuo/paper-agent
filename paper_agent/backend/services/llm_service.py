import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
import asyncio
from abc import ABC, abstractmethod
import json

from backend.config.settings import settings

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_summary(self, text: str, max_length: int, style: str) -> str:
        """Generate summary for given text."""
        pass
    
    @abstractmethod
    async def generate_response(self, prompt: str, max_tokens: int) -> str:
        """Generate response for given prompt."""
        pass
    
    @abstractmethod
    async def generate_streaming_response(self, prompt: str, max_tokens: int) -> AsyncGenerator[str, None]:
        """Generate streaming response for given prompt."""
        pass

class HuggingFaceProvider(LLMProvider):
    """Hugging Face transformers provider."""
    
    def __init__(self):
        self.model_name = settings.llm.model
        self.temperature = settings.llm.temperature
        self.max_tokens = settings.llm.max_tokens
        self._pipeline = None
    
    def _get_pipeline(self):
        """Lazy load the pipeline."""
        if self._pipeline is None:
            try:
                from transformers import pipeline
                
                # Use a smaller model for local development
                model_name = "facebook/bart-large-cnn"  # Good for summarization
                
                self._pipeline = pipeline(
                    "summarization",
                    model=model_name,
                    tokenizer=model_name,
                    device=-1  # Use CPU
                )
            except Exception as e:
                logger.error(f"Error loading Hugging Face model: {str(e)}")
                raise
    
    async def generate_summary(self, text: str, max_length: int, style: str) -> str:
        """Generate summary using Hugging Face transformers."""
        self._get_pipeline()
        
        try:
            # Limit input text length
            max_input_length = 1024
            if len(text) > max_input_length:
                text = text[:max_input_length]
            
            # Generate summary
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._pipeline(
                    text,
                    max_length=max_length,
                    min_length=min(50, max_length // 2),
                    do_sample=False
                )
            )
            
            summary = result[0]['summary_text']
            
            # Adjust style
            if style == "simple":
                summary = self._simplify_text(summary)
            elif style == "detailed":
                summary = self._add_details(summary, text)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return self._fallback_summary(text, max_length)
    
    async def generate_response(self, prompt: str, max_tokens: int) -> str:
        """Generate response using Hugging Face transformers."""
        # For now, use a simple response
        return f"Response to: {prompt[:100]}..."
    
    async def generate_streaming_response(self, prompt: str, max_tokens: int) -> AsyncGenerator[str, None]:
        """Generate streaming response using Hugging Face transformers."""
        # For now, simulate streaming by yielding chunks
        response = await self.generate_response(prompt, max_tokens)
        for i in range(0, len(response), 10):
            yield response[i:i+10]
            await asyncio.sleep(0.1)  # Simulate processing time
    
    def _simplify_text(self, text: str) -> str:
        """Simplify text for non-technical readers."""
        # Basic simplification
        text = text.replace("methodology", "method")
        text = text.replace("utilize", "use")
        text = text.replace("demonstrate", "show")
        text = text.replace("subsequently", "then")
        return text
    
    def _add_details(self, summary: str, original_text: str) -> str:
        """Add more details to summary."""
        # For now, just return the summary
        return summary
    
    def _fallback_summary(self, text: str, max_length: int) -> str:
        """Fallback summary generation."""
        sentences = text.split('. ')
        summary = ""
        for sentence in sentences:
            if len(summary) + len(sentence) < max_length:
                summary += sentence + '. '
            else:
                break
        
        return summary.strip()

class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(self):
        self.api_key = settings.llm.api_key
        self.model = settings.llm.model
        self.temperature = settings.llm.temperature
        self.max_tokens = settings.llm.max_tokens
    
    async def generate_summary(self, text: str, max_length: int, style: str) -> str:
        """Generate summary using OpenAI API."""
        try:
            import openai
            openai.api_key = self.api_key
            
            # Prepare prompt based on style
            if style == "academic":
                prompt = f"Please provide a concise academic summary of the following research paper:\n\n{text}\n\nSummary (max {max_length} characters):"
            elif style == "simple":
                prompt = f"Please provide a simple, easy-to-understand summary of the following text:\n\n{text}\n\nSummary (max {max_length} characters):"
            else:  # detailed
                prompt = f"Please provide a detailed summary of the following research paper, including key findings and methodology:\n\n{text}\n\nSummary (max {max_length} characters):"
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_length,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {str(e)}")
            return self._fallback_summary(text, max_length)
    
    async def generate_response(self, prompt: str, max_tokens: int) -> str:
        """Generate response using OpenAI API."""
        try:
            import openai
            openai.api_key = self.api_key
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response with OpenAI: {str(e)}")
            return "Sorry, I encountered an error generating a response."
    
    async def generate_streaming_response(self, prompt: str, max_tokens: int) -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenAI API."""
        try:
            import openai
            openai.api_key = self.api_key
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant that thinks step by step."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=self.temperature,
                stream=True
            )
            
            async for chunk in response:
                if 'choices' in chunk and len(chunk.choices) > 0:
                    content = chunk.choices[0].delta.get("content", "")
                    if content:
                        yield content
                        
        except Exception as e:
            logger.error(f"Error generating streaming response with OpenAI: {str(e)}")
            yield "Sorry, I encountered an error generating a response."

class QwenProvider(LLMProvider):
    """Qwen (Tongyi) API provider."""
    
    def __init__(self):
        self.api_key = settings.llm.qwen_api_key
        self.model = settings.llm.qwen_model or "qwen-plus"
        self.temperature = settings.llm.temperature
        self.max_tokens = settings.llm.max_tokens
    
    async def generate_summary(self, text: str, max_length: int, style: str) -> str:
        """Generate summary using Qwen API."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            
            # Prepare prompt based on style
            if style == "academic":
                prompt = f"Please provide a concise academic summary of the following research paper:\n\n{text}\n\nSummary (max {max_length} characters):"
            elif style == "simple":
                prompt = f"Please provide a simple, easy-to-understand summary of the following text:\n\n{text}\n\nSummary (max {max_length} characters):"
            else:  # detailed
                prompt = f"Please provide a detailed summary of the following research paper, including key findings and methodology:\n\n{text}\n\nSummary (max {max_length} characters):"
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_length,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary with Qwen: {str(e)}")
            return self._fallback_summary(text, max_length)
    
    async def generate_response(self, prompt: str, max_tokens: int) -> str:
        """Generate response using Qwen API."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response with Qwen: {str(e)}")
            return "Sorry, I encountered an error generating a response."
    
    async def generate_streaming_response(self, prompt: str, max_tokens: int) -> AsyncGenerator[str, None]:
        """Generate streaming response using Qwen API."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant that thinks step by step."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=self.temperature,
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                        
        except Exception as e:
            logger.error(f"Error generating streaming response with Qwen: {str(e)}")
            yield "Sorry, I encountered an error generating a response."

class DeepSeekProvider(LLMProvider):
    """DeepSeek API provider."""
    
    def __init__(self):
        self.api_key = settings.llm.deepseek_api_key
        self.model = settings.llm.deepseek_model or "deepseek-chat"
        self.temperature = settings.llm.temperature
        self.max_tokens = settings.llm.max_tokens
    
    async def generate_summary(self, text: str, max_length: int, style: str) -> str:
        """Generate summary using DeepSeek API."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com/v1"
            )
            
            # Prepare prompt based on style
            if style == "academic":
                prompt = f"Please provide a concise academic summary of the following research paper:\n\n{text}\n\nSummary (max {max_length} characters):"
            elif style == "simple":
                prompt = f"Please provide a simple, easy-to-understand summary of the following text:\n\n{text}\n\nSummary (max {max_length} characters):"
            else:  # detailed
                prompt = f"Please provide a detailed summary of the following research paper, including key findings and methodology:\n\n{text}\n\nSummary (max {max_length} characters):"
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_length,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary with DeepSeek: {str(e)}")
            return self._fallback_summary(text, max_length)
    
    async def generate_response(self, prompt: str, max_tokens: int) -> str:
        """Generate response using DeepSeek API."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com/v1"
            )
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response with DeepSeek: {str(e)}")
            return "Sorry, I encountered an error generating a response."
    
    async def generate_streaming_response(self, prompt: str, max_tokens: int) -> AsyncGenerator[str, None]:
        """Generate streaming response using DeepSeek API."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com/v1"
            )
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant that thinks step by step."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=self.temperature,
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                        
        except Exception as e:
            logger.error(f"Error generating streaming response with DeepSeek: {str(e)}")
            yield "Sorry, I encountered an error generating a response."

class OllamaProvider(LLMProvider):
    """Ollama API provider."""
    
    def __init__(self):
        self.model = settings.llm.ollama_model or "llama3"
        self.base_url = settings.llm.ollama_base_url or "http://localhost:11434/v1"
        self.temperature = settings.llm.temperature
        self.max_tokens = settings.llm.max_tokens
    
    async def generate_summary(self, text: str, max_length: int, style: str) -> str:
        """Generate summary using Ollama API."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                base_url=self.base_url,
                api_key="ollama"  # Required but unused for Ollama
            )
            
            # Prepare prompt based on style
            if style == "academic":
                prompt = f"Please provide a concise academic summary of the following research paper:\n\n{text}\n\nSummary (max {max_length} characters):"
            elif style == "simple":
                prompt = f"Please provide a simple, easy-to-understand summary of the following text:\n\n{text}\n\nSummary (max {max_length} characters):"
            else:  # detailed
                prompt = f"Please provide a detailed summary of the following research paper, including key findings and methodology:\n\n{text}\n\nSummary (max {max_length} characters):"
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_length,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary with Ollama: {str(e)}")
            return self._fallback_summary(text, max_length)
    
    async def generate_response(self, prompt: str, max_tokens: int) -> str:
        """Generate response using Ollama API."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                base_url=self.base_url,
                api_key="ollama"  # Required but unused for Ollama
            )
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response with Ollama: {str(e)}")
            return "Sorry, I encountered an error generating a response."
    
    async def generate_streaming_response(self, prompt: str, max_tokens: int) -> AsyncGenerator[str, None]:
        """Generate streaming response using Ollama API."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                base_url=self.base_url,
                api_key="ollama"  # Required but unused for Ollama
            )
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant that thinks step by step."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=self.temperature,
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                        
        except Exception as e:
            logger.error(f"Error generating streaming response with Ollama: {str(e)}")
            yield "Sorry, I encountered an error generating a response."

class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""
    
    def __init__(self):
        self.api_key = settings.llm.anthropic_api_key
        self.model = settings.llm.anthropic_model or "claude-3-haiku-20240307"
        self.temperature = settings.llm.temperature
        self.max_tokens = settings.llm.max_tokens
    
    async def generate_summary(self, text: str, max_length: int, style: str) -> str:
        """Generate summary using Anthropic Claude API."""
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.api_key)
            
            # Prepare prompt based on style
            if style == "academic":
                prompt = f"Please provide a concise academic summary of the following research paper:\n\n{text}\n\nSummary (max {max_length} characters):"
            elif style == "simple":
                prompt = f"Please provide a simple, easy-to-understand summary of the following text:\n\n{text}\n\nSummary (max {max_length} characters):"
            else:  # detailed
                prompt = f"Please provide a detailed summary of the following research paper, including key findings and methodology:\n\n{text}\n\nSummary (max {max_length} characters):"
            
            response = await client.messages.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_length,
                temperature=self.temperature
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary with Anthropic: {str(e)}")
            return self._fallback_summary(text, max_length)
    
    async def generate_response(self, prompt: str, max_tokens: int) -> str:
        """Generate response using Anthropic Claude API."""
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.api_key)
            
            response = await client.messages.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=self.temperature
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Error generating response with Anthropic: {str(e)}")
            return "Sorry, I encountered an error generating a response."
    
    async def generate_streaming_response(self, prompt: str, max_tokens: int) -> AsyncGenerator[str, None]:
        """Generate streaming response using Anthropic Claude API."""
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.api_key)
            
            response = await client.messages.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": f"Think step by step and show your thinking process. Then answer the following question:\n\n{prompt}"}
                ],
                max_tokens=max_tokens,
                temperature=self.temperature,
                stream=True
            )
            
            async for chunk in response:
                if hasattr(chunk, 'type') and chunk.type == "content_block_delta":
                    yield chunk.delta.text
                    
        except Exception as e:
            logger.error(f"Error generating streaming response with Anthropic: {str(e)}")
            yield "Sorry, I encountered an error generating a response."

class LLMService:
    """Main LLM service that delegates to appropriate provider."""
    
    def __init__(self):
        self.provider = self._create_provider()
    
    def _create_provider(self) -> LLMProvider:
        """Create appropriate LLM provider based on configuration."""
        provider_type = settings.llm.provider.lower()
        
        if provider_type == "huggingface":
            return HuggingFaceProvider()
        elif provider_type == "openai":
            if not settings.llm.api_key:
                logger.warning("OpenAI API key not provided, falling back to HuggingFace")
                return HuggingFaceProvider()
            return OpenAIProvider()
        elif provider_type == "qwen":
            if not settings.llm.qwen_api_key:
                logger.warning("Qwen API key not provided, falling back to HuggingFace")
                return HuggingFaceProvider()
            return QwenProvider()
        elif provider_type == "deepseek":
            if not settings.llm.deepseek_api_key:
                logger.warning("DeepSeek API key not provided, falling back to HuggingFace")
                return HuggingFaceProvider()
            return DeepSeekProvider()
        elif provider_type == "ollama":
            return OllamaProvider()
        elif provider_type == "anthropic":
            if not settings.llm.anthropic_api_key:
                logger.warning("Anthropic API key not provided, falling back to HuggingFace")
                return HuggingFaceProvider()
            return AnthropicProvider()
        else:
            logger.warning(f"Unknown provider {provider_type}, using HuggingFace")
            return HuggingFaceProvider()
    
    async def generate_summary(self, text: str, max_length: int = 300, style: str = "academic") -> str:
        """Generate summary for document."""
        if not text or len(text.strip()) < 50:
            return "Text too short to generate meaningful summary."
        
        try:
            return await self.provider.generate_summary(text, max_length, style)
        except Exception as e:
            logger.error(f"Error in generate_summary: {str(e)}")
            return self._generate_basic_summary(text, max_length)
    
    async def answer_question(self, question: str, context: str) -> str:
        """Answer question based on document context."""
        prompt = f"""Based on the following document, please answer the question:

Document: {context[:2000]}...

Question: {question}

Answer:"""
        
        try:
            return await self.provider.generate_response(prompt, max_tokens=300)
        except Exception as e:
            logger.error(f"Error in answer_question: {str(e)}")
            return "Sorry, I couldn't generate an answer."
    
    async def generate_recommendations(self, user_history: List[str], available_docs: List[Dict[str, Any]]) -> List[str]:
        """Generate document recommendations based on user history."""
        if not user_history or not available_docs:
            return []
        
        prompt = f"""Based on the user's reading history:
{chr(10).join(user_history[:5])}

Recommend the most relevant documents from the following:
{chr(10).join([doc['title'] for doc in available_docs[:10]])}

Provide 3-5 recommendations with brief explanations."""
        
        try:
            response = await self.provider.generate_response(prompt, max_tokens=400)
            return response.split('\n')
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    async def generate_streaming_response(self, prompt: str, max_tokens: int = 500) -> AsyncGenerator[str, None]:
        """Generate streaming response for given prompt."""
        try:
            async for chunk in self.provider.generate_streaming_response(prompt, max_tokens):
                yield chunk
        except Exception as e:
            logger.error(f"Error in generate_streaming_response: {str(e)}")
            yield "Sorry, I encountered an error generating a response."
    
    def _generate_basic_summary(self, text: str, max_length: int) -> str:
        """Generate basic summary without LLM."""
        sentences = text.split('. ')
        summary = ""
        word_count = 0
        
        for sentence in sentences:
            words = sentence.split()
            if word_count + len(words) < max_length // 5:  # Rough estimate
                summary += sentence + '. '
                word_count += len(words)
            else:
                break
        
        if not summary:
            summary = text[:max_length] + "..." if len(text) > max_length else text
        
        return summary.strip()