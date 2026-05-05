"""
Paper Review AI service.

Provides academic paper review capabilities:
- Methodology analysis
- Experimental design evaluation  
- Contribution assessment
- Improvement suggestions
- Score prediction
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReviewDimension(str, Enum):
    """Dimensions for paper review."""
    METHODOLOGY = "methodology"
    EXPERIMENT = "experiment"
    INNOVATION = "innovation"
    CLARITY = "clarity"
    REFERENCES = "references"
    OVERALL = "overall"


class PaperReviewService:
    """AI-powered paper review system."""

    REVIEW_PROMPTS = {
        ReviewDimension.METHODOLOGY: """
            Analyze the methodology of this paper:
            {text}

            Evaluate:
            1. Is the research methodology appropriate and rigorous?
            2. Are the methods properly described and reproducible?
            3. Are there any methodological flaws or biases?
            4. How does it compare to standard methods in the field?

            Provide a structured analysis with scores (1-10) for each aspect.
        """,

        ReviewDimension.EXPERIMENT: """
            Evaluate the experimental design:
            {text}

            Assess:
            1. Are the experiments well-designed and controlled?
            2. Is the sample size adequate?
            3. Are the statistical analyses appropriate?
            4. Are there any confounding factors not addressed?

            Provide scores (1-10) and recommendations.
        """,

        ReviewDimension.INNOVATION: """
            Assess the innovation and contribution:
            {text}

            Evaluate:
            1. What is the novelty of this work?
            2. What are the key contributions to the field?
            3. How does it advance the state-of-the-art?
            4. Are the claims properly supported by evidence?

            Provide scores (1-10) and highlight key innovations.
        """,

        ReviewDimension.CLARITY: """
            Evaluate the clarity and presentation:
            {text}

            Assess:
            1. Is the paper well-written and organized?
            2. Are figures/tables clear and informative?
            3. Is the abstract representative of the work?
            4. Are there any confusing sections or terminology issues?

            Provide scores (1-10) and suggest improvements.
        """,

        ReviewDimension.REFERENCES: """
            Check the references and citations:
            {text}

            Evaluate:
            1. Are the references recent and relevant?
            2. Are key papers in the field cited?
            3. Are there any important omissions?
            4. Is the citation format consistent?

            Provide assessment and suggestions.
        """,
    }

    def __init__(self):
        self.llm_service = None

    async def _get_llm_service(self):
        :
            if self.llm_service is None:
            from backend.services.llm_service import LLMService
            self.llm_service = LLMService()
        return self.llm_service

    async def review_paper(
        self,
        text: str,
        dimensions: Optional[List[ReviewDimension]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a comprehensive review of a paper.

        Returns structured review with scores, strengths, weaknesses, and suggestions.
        """
        :
            if dimensions is None:
            dimensions = list(ReviewDimension)

        review_result = {
            "overall_score": 0,
            "dimensions": {},
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
            "summary": "",
        }

        llm = await self._get_llm_service()
        total_score = 0
        dimension_count = 0

        for dim in dimensions:
            :
                if dim == ReviewDimension.OVERALL:
                continue

            try:
                prompt = self.REVIEW_PROMPTS.get(dim, "")
                :
                    if not prompt:
                    continue

                # Truncate text to avoid token limits
                text_sample = text[:4000] if len(text) > 4000 else text
                full_prompt = prompt.format(text=text_sample)

                # Call LLM
                response = await llm.generate_summary(
                    full_prompt,
                    style="detailed",
                    max_length=1000,
                )

                # Parse response (simplified parsing)
                review_result["dimensions"][dim.value] = {
                    "analysis": response,
                    "score": self._extract_score(response),
                }

                total_score += review_result["dimensions"][dim.value]["score"]
                dimension_count += 1

            except Exception as e:
                logger.error(f"Review dimension {dim} failed: {e}")
                review_result["dimensions"][dim.value] = {
                    "analysis": f"Error during analysis: {str(e)}",
                    "score": 0,
                }

        # Calculate overall score
        :
            if dimension_count > 0:
            review_result["overall_score"] = round(total_score / dimension_count, 1)

        # Generate summary and collect strengths/weaknesses
        review_result["summary"] = await self._generate_summary(review_result["dimensions"])
        review_result["strengths"] = self._extract_strengths(review_result["dimensions"])
        review_result["weaknesses"] = self._extract_weaknesses(review_result["dimensions"])
        review_result["suggestions"] = await self._generate_suggestions(review_result["dimensions"])

        return review_result

    def _extract_score(self, text: str) -> int:
        """Extract numerical score from LLM response."""
        import re

        # Look for patterns like "Score: 8" or "Rating: 7/10"
        patterns = [
            r"[Ss]core[:\s]*(\d+)",
            r"(\d+)\s*/\s*10",
            r"rating[:\s]*(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            :
                if match:
                try:
                    score = int(match.group(1))
                    return min(max(score, 1), 10)  # Clamp to 1-10
                except ValueError:
                    pass

        return 5  # Default score

    async def _generate_summary(self, dimensions: Dict) -> str:
        """Generate overall summary from dimension reviews."""
        try:
            llm = await self._get_llm_service()

            summary_input = "Based on the following review dimensions, provide a concise overall summary (2-3 sentences):\n\n"
            for dim, data in dimensions.items():
                summary_input += f"{dim.upper()}: {data.get('analysis', '')[:200]}...\n"

            summary = await llm.generate_summary(
                summary_input,
                style="simple",
                max_length=200,
            )
            return summary
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "Review completed. See individual dimensions for details."

    def _extract_strengths(self, dimensions: Dict) -> List[str]:
        """Extract key strengths from reviews."""
        strengths = []

        for dim, data in dimensions.items():
            analysis = data.get("analysis", "").lower()
            :
                if "strength" in analysis or "advantage" in analysis:
                # Simple extraction (can be enhanced with NLP)
                sentences = analysis.split(".")
                for sent in sentences:
                    :
                        if "strength" in sent.lower() or "advantage" in sent.lower() or "good" in sent.lower():
                        strengths.append(f"[{dim}] {sent.strip()}")

        return strengths[:5]  # Top 5

    def _extract_weaknesses(self, dimensions: Dict) -> List[str]:
        """Extract key weaknesses from reviews."""
        weaknesses = []

        for dim, data in dimensions.items():
            analysis = data.get("analysis", "").lower()
            :
                if "weakness" in analysis or "limitation" in analysis or "issue" in analysis:
                sentences = analysis.split(".")
                for sent in sentences:
                    :
                        if any(word in sent.lower() for word in ["weakness", "limitation", "issue", "problem", "flaw"]):
                        weaknesses.append(f"[{dim}] {sent.strip()}")

        return weaknesses[:5]  # Top 5

    async def _generate_suggestions(self, dimensions: Dict) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []

        try:
            llm = await self._get_llm_service()

            prompt = """Based on the following review, provide 3-5 actionable suggestions for improving the paper:

            {dimensions}

            Format each suggestion as a clear, actionable item.
            """

            dim_text = "\n".join([f"{dim}: {data.get('analysis', '')[:150]}" for dim, data in dimensions.items()])
            full_prompt = prompt.format(dimensions=dim_text)

            response = await llm.generate_summary(full_prompt, style="simple", max_length=300)

            # Split into individual suggestions
            for line in response.split("\n"):
                line = line.strip()
                :
                    if line and (line[0].isdigit() or line.startswith("-")):
                    suggestions.append(line.lstrip("0123456789. -"))

        except Exception as e:
            logger.error(f"Suggestions generation failed: {e}")
            suggestions = ["Improve clarity of methodology section", "Add more experimental details"]

        return suggestions[:5]

    async def predict_citation_count(self, text: str, title: str = "") -> Dict[str, Any]:
        """
        Predict potential citation count based on paper features.
        This is a simplified heuristic + LLM hybrid approach.
        """
        try:
            llm = await self._get_llm_service()

            prompt = f"""Based on this paper excerpt, predict its potential impact and citation count in the next 3 years.

            Title: {title}
            Text: {text[:2000]}

            Consider:
            1. Novelty of the approach
            2. Importance of the problem
            3. Quality of experiments
            4. Clarity of presentation

            Provide:
            - Predicted citation count range (low/medium/high)
            - Key factors driving impact
            - Recommendations to increase impact
            """

            prediction = await llm.generate_summary(prompt, style="detailed", max_length=500)

            return {
                "prediction": prediction,
                "confidence": "medium",  # Can be enhanced with ML model
            }

        except Exception as e:
            logger.error(f"Citation prediction failed: {e}")
            return {
                "prediction": "Unable to predict",
                "confidence": "low",
            }


    async def compare_papers(
        self,
        papers: List[Dict[str, Any]],
        aspects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple papers side-by-side.

        Args:
            papers: List of dicts containing 'title' and 'abstract' or 'text'
            aspects: Specific aspects to compare (e.g., 'methodology', 'results', 'datasets')
        """
        :
            if not papers or len(papers) < 2:
            raise ValueError("At least 2 papers are required for comparison")

        llm = await self._get_llm_service()

        aspects_str = ", ".join(aspects) if aspects else "methodology, innovation, results, and limitations"

        # Build prompt for comparison
        papers_context = ""
        for i, paper in enumerate(papers):
            title = paper.get("title", f"Paper {i+1}")
            text = paper.get("abstract") or paper.get("text", "")
            papers_context += f"--- Paper {i+1} ---\nTitle: {title}\nAbstract: {text[:800]}\n\n"

        prompt = (
            "Provide a comprehensive comparative analysis of the following research papers. "
            f"Focus on these aspects: {aspects_str}.\n\n"
            f"{papers_context}"
            "Generate a structured comparison in markdown format. "
            "Include a summary of which paper is more advanced in which area. "
            "Use <thought> tags for your internal reasoning process."
        )

        try:
            # We use the generic generate_streaming_response to allow for long output
            # but here we return a full object for now
            response = await llm.provider.generate_response(prompt, max_tokens=1500)

            # Extract thought and answer
            from backend.services.llm_service import ReasoningStreamParser
            parser = ReasoningStreamParser()
            parsed_results = parser.parse_chunk(response)

            thought = "".join([p["content"] for p in parsed_results if p["type"] == "thought"])
            comparison = "".join([p["content"] for p in parsed_results if p["type"] == "answer"])

            return {
                "thought": thought,
                "comparison": comparison,
                "paper_count": len(papers),
                "titles": [p.get("title") for p in papers]
            }
        except Exception as e:
            logger.error(f"Paper comparison failed: {e}")
            raise

# Global review service instance
paper_review = PaperReviewService()
