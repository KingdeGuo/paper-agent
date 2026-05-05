"""
Downstream Research Services — capabilities for after you've read the papers.

Covers: code generation, expression validation, data checking, experiment design,
manuscript formatting, figure generation, review responses, patent/grant writing.
"""

import logging
from typing import Any, Dict, List

from backend.services.registry import get_llm_service

logger = logging.getLogger(__name__)


class DownstreamService:
    """Suite of downstream research capabilities."""

    # ─── 1. Code Generator ────────────────────────────────────

    async def generate_code(self, paper_text: str, language: str = "python",
                            task: str = "implement the main algorithm") -> Dict[str, Any]:
        """Generate implementation code from a paper's methodology."""
        llm = get_llm_service()
        if not llm:
            return {"code": "", "error": "LLM not available"}

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content":
                    f"Based on this paper, {task} in {language}.\n\nPaper:\n{paper_text[:3000]}\n\n"
                    f"Generate complete, runnable {language} code. Include:\n"
                    f"1. Full implementation\n2. Comments explaining key steps\n3. Example usage\n4. Dependencies needed"}],
                system_prompt=f"You are a research engineer implementing algorithms from papers. Generate production-quality {language} code with proper error handling and docstrings.",
            )
            code = resp.get("content", "") if isinstance(resp, dict) else str(resp)
            return {"code": code, "language": language, "task": task, "lines": len(code.split('\n'))}
        except Exception as e:
            return {"code": "", "error": str(e)}

    async def generate_code_from_formula(self, formula: str, language: str = "python") -> Dict[str, Any]:
        """Generate code for a specific mathematical formula."""
        llm = get_llm_service()
        if not llm:
            return {"code": ""}

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content":
                    f"Implement this mathematical formula in {language}:\n\n{formula}\n\n"
                    f"Return complete {language} code that computes this formula. Include test cases."}],
                system_prompt=f"You translate mathematical formulas into {language} code. Be precise and numerically stable.",
            )
            return {"code": resp.get("content", ""), "language": language, "formula": formula}
        except Exception as e:
            return {"code": "", "error": str(e)}

    # ─── 2. Expression Validator ──────────────────────────────

    async def validate_expression(self, expression: str, context: str = "") -> Dict[str, Any]:
        """Validate a mathematical expression or derivation for correctness."""
        llm = get_llm_service()
        if not llm:
            return {"valid": None, "error": "LLM not available"}

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content":
                    f"Analyze this mathematical expression/derivation for correctness:\n\n{expression}\n\n"
                    f"{'Context: ' + context[:1000] if context else ''}\n\n"
                    f"Check: 1) Dimensional consistency 2) Algebraic correctness 3) Sign errors "
                    f"4) Boundary conditions 5) Numerical stability. "
                    f"Flag any issues and suggest corrections."}],
                system_prompt="You are a mathematical physicist reviewing derivations. Be rigorous and precise.",
            )
            analysis = resp.get("content", "") if isinstance(resp, dict) else str(resp)
            has_error = any(w in analysis.lower() for w in ["error", "incorrect", "wrong", "mistake", "issue"])
            return {
                "expression": expression,
                "analysis": analysis,
                "has_issues": has_error,
                "confidence": "high" if not has_error else "medium",
            }
        except Exception as e:
            return {"valid": None, "error": str(e)}

    # ─── 3. Data Accuracy Checker ─────────────────────────────

    async def check_data_accuracy(self, data_claims: str, context: str = "") -> Dict[str, Any]:
        """Cross-validate numerical claims against paper context."""
        llm = get_llm_service()
        if not llm:
            return {"error": "LLM not available"}

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content":
                    f"Cross-validate these data claims for consistency and accuracy:\n\nClaims:\n{data_claims[:2000]}\n\n"
                    f"{'Paper Context:\n' + context[:1500] if context else ''}\n\n"
                    f"Check: 1) Internal consistency 2) Statistical plausibility "
                    f"3) Order-of-magnitude correctness 4) Unit consistency 5) Citation accuracy. "
                    f"Flag any numbers that seem off."}],
                system_prompt="You are a research integrity analyst. Verify numerical claims rigorously.",
            )
            return {
                "claims": data_claims[:500],
                "analysis": resp.get("content", ""),
                "verified": True,
            }
        except Exception as e:
            return {"error": str(e)}

    # ─── 4. Experiment Designer ───────────────────────────────

    async def design_experiment(self, methodology: str, resources: str = "",
                                 constraints: str = "") -> Dict[str, Any]:
        """Design experiments based on paper methodology."""
        llm = get_llm_service()
        if not llm:
            return {"error": "LLM not available"}

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content":
                    f"Based on this methodology, design a detailed experiment:\n\nMethodology:\n{methodology[:2000]}\n\n"
                    f"{'Resources available: ' + resources[:500] if resources else ''}\n"
                    f"{'Constraints: ' + constraints[:500] if constraints else ''}\n\n"
                    f"Provide:\n1. Experimental setup\n2. Required materials/datasets\n3. Key variables to measure\n"
                    f"4. Control conditions\n5. Expected outcomes\n6. Success criteria\n7. Potential confounders"}],
                system_prompt="You are an experimental design expert. Design rigorous, reproducible experiments.",
            )
            return {
                "design": resp.get("content", ""),
                "methodology": methodology[:200],
            }
        except Exception as e:
            return {"error": str(e)}

    # ─── 5. Manuscript Formatter ──────────────────────────────

    async def format_manuscript(self, content: str, template: str = "arxiv",
                                 title: str = "", authors: List[str] = None) -> Dict[str, Any]:
        """Format content to journal LaTeX templates."""
        templates = {
            "arxiv": {
                "name": "arXiv / Standard LaTeX",
                "preamble": r"\documentclass[11pt]{article}\usepackage[utf8]{inputenc}\usepackage{amsmath,amssymb}",
            },
            "neurips": {
                "name": "NeurIPS",
                "preamble": r"\documentclass{article}\usepackage[neurips]{jmlr2e}",
            },
            "icml": {
                "name": "ICML",
                "preamble": r"\documentclass{article}\usepackage{icml2024}",
            },
            "acl": {
                "name": "ACL",
                "preamble": r"\documentclass[11pt]{article}\usepackage{acl}",
            },
            "ieee": {
                "name": "IEEE",
                "preamble": r"\documentclass[conference]{IEEEtran}",
            },
        }
        tmpl = templates.get(template, templates["arxiv"])

        authors_str = "\\and ".join(authors) if authors else "Author"

        latex = f"""{tmpl['preamble']}

\\title{{{title or 'Untitled'}}}

\\author{{{authors_str}}}

\\begin{{document}}
\\maketitle

{content}

\\end{{document}}
"""
        return {"latex": latex, "template": template, "template_name": tmpl['name']}

    # ─── 6. Figure Generator ──────────────────────────────────

    async def generate_figure_code(self, data_description: str, chart_type: str = "matplotlib",
                                    style: str = "publication") -> Dict[str, Any]:
        """Generate Python code for creating publication-quality figures."""
        llm = get_llm_service()
        if not llm:
            return {"code": ""}

        style_configs = {
            "publication": "Nature/Science style: clean, minimal, high DPI, accessible colors",
            "presentation": "Conference presentation: larger fonts, bolder colors, readable from distance",
            "poster": "Poster session: very large fonts, high contrast, simplified design",
        }
        style_desc = style_configs.get(style, style_configs["publication"])

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content":
                    f"Generate Python code to create a {chart_type} figure for: {data_description}\n\n"
                    f"Style: {style_desc}\n\n"
                    f"Include:\n1. Full runnable code with sample data\n2. Proper axis labels and titles\n"
                    f"3. Color scheme suitable for publication\n4. Legend placement\n"
                    f"5. Save as high-res PDF/PNG\n6. Error bars where appropriate"}],
                system_prompt=f"You generate publication-quality {chart_type} visualization code in Python.",
            )
            return {
                "code": resp.get("content", ""),
                "chart_type": chart_type,
                "style": style,
            }
        except Exception as e:
            return {"code": "", "error": str(e)}

    # ─── 7. Review Response Generator ─────────────────────────

    async def generate_review_response(self, reviewer_comments: str, paper_summary: str = "",
                                        tone: str = "professional") -> Dict[str, Any]:
        """Draft point-by-point responses to reviewer comments."""
        llm = get_llm_service()
        if not llm:
            return {"error": "LLM not available"}

        tone_guides = {
            "professional": "Be respectful, thorough, and constructive",
            "detailed": "Provide extensive technical justification for each response",
            "concise": "Keep responses brief but complete",
        }
        tone_guide = tone_guides.get(tone, tone_guides["professional"])

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content":
                    f"Draft a point-by-point response to these reviewer comments:\n\n"
                    f"Reviewer Comments:\n{reviewer_comments[:3000]}\n\n"
                    f"{'Paper Summary:\n' + paper_summary[:1000] if paper_summary else ''}\n\n"
                    f"Style: {tone_guide}\n\n"
                    f"For each comment, provide:\n1. The reviewer's comment (quoted)\n2. Your response\n"
                    f"3. What was changed in the manuscript\n4. Page/line references"}],
                system_prompt="You are an experienced academic writing mentor helping authors respond to peer review.",
            )
            return {
                "responses": resp.get("content", ""),
                "comments_count": reviewer_comments.count("Comment") or reviewer_comments.count("comment"),
                "tone": tone,
            }
        except Exception as e:
            return {"error": str(e)}

    # ─── 8. Patent Idea Extractor ──────────────────────────────

    async def extract_patent_ideas(self, paper_text: str) -> Dict[str, Any]:
        """Identify patentable ideas and innovations from research papers."""
        llm = get_llm_service()
        if not llm:
            return {"error": "LLM not available"}

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content":
                    f"Analyze this research paper and identify patentable innovations:\n\n{paper_text[:3000]}\n\n"
                    f"Identify:\n1. Novel technical innovations (be specific)\n2. Prior art differentiation\n"
                    f"3. Commercial applications\n4. Key claims for a patent\n"
                    f"5. Technical field classification\n6. Inventive step justification"}],
                system_prompt="You are a patent attorney specializing in technology. Identify patentable subject matter rigorously.",
            )
            return {
                "analysis": resp.get("content", ""),
            }
        except Exception as e:
            return {"error": str(e)}

    # ─── 9. Grant Proposal Writer ─────────────────────────────

    async def write_grant_proposal(self, topic: str, funding_agency: str = "NSF",
                                    pi_background: str = "", budget: str = "") -> Dict[str, Any]:
        """Draft a research grant proposal based on papers and research direction."""
        llm = get_llm_service()
        if not llm:
            return {"error": "LLM not available"}

        agency_guides = {
            "NSF": "NSF format: intellectual merit, broader impacts, 15-page limit",
            "NIH": "NIH format: specific aims, research strategy, significance, innovation, approach",
            "ERC": "ERC format: state-of-the-art, methodology, resources, impact",
            "horizon": "Horizon Europe: excellence, impact, quality of implementation",
        }
        guide = agency_guides.get(funding_agency, agency_guides["NSF"])

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content":
                    f"Draft a grant proposal on: {topic}\n\n"
                    f"Funding agency: {funding_agency} ({guide})\n"
                    f"{'PI Background: ' + pi_background[:500] if pi_background else ''}\n"
                    f"{'Budget: ' + budget[:500] if budget else ''}\n\n"
                    f"Write:\n1. Title and abstract\n2. Specific aims / research questions\n"
                    f"3. Background and significance\n4. Innovation (what makes this novel)\n"
                    f"5. Research approach / methodology\n6. Expected outcomes\n7. Timeline"}],
                system_prompt=f"You are an expert grant writer. Write compelling, fundable proposals in {funding_agency} format.",
            )
            return {
                "proposal": resp.get("content", ""),
                "agency": funding_agency,
                "topic": topic,
            }
        except Exception as e:
            return {"error": str(e)}


# Global service
downstream = DownstreamService()
