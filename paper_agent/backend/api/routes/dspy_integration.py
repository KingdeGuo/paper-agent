"""
DSPy Integration — optimizable AI pipelines for research tasks.

Reference: Stanford DSPy (github.com/stanfordnlp/dspy)
Enables DSPy-style programming of LLM pipelines within Paper Agent.
"""

import logging
from typing import Any, Dict, List

from backend.services.registry import get_llm_service
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── DSPy-style Signatures ────────────────────────────────

SIGNATURES = {
    "summarize": {
        "description": "Summarize academic paper content",
        "inputs": {"text": "Paper text"},
        "outputs": {"summary": "Concise summary", "key_points": ["Key findings"]},
        "template": "Summarize this academic paper. Provide a concise summary and 3-5 key points.\n\nText: {text}\n\nSummary:",
    },
    "extract_findings": {
        "description": "Extract structured findings from papers",
        "inputs": {"text": "Paper text"},
        "outputs": {
            "problem": "Research problem",
            "method": "Methodology",
            "results": ["Key results"],
            "limitations": ["Limitations"],
        },
        "template": "Extract structured findings from this paper.\n\nResearch problem:\nMethodology:\nKey results (list):\nLimitations (list):\n\nText: {text}",
    },
    "compare_papers": {
        "description": "Compare multiple papers",
        "inputs": {"papers": "List of paper descriptions"},
        "outputs": {"comparison": "Structured comparison", "recommendations": "Recommendations"},
        "template": "Compare the following papers. Highlight similarities, differences, and provide recommendations.\n\nPapers:\n{papers}\n\nComparison:\nRecommendations:",
    },
    "identify_gaps": {
        "description": "Identify research gaps",
        "inputs": {"papers": "List of paper summaries"},
        "outputs": {"gaps": ["Research gaps"], "hypotheses": ["Novel hypotheses"]},
        "template": "Analyze these papers and identify:\n1. Research gaps (what's missing)\n2. Novel research hypotheses\n\nPapers:\n{papers}",
    },
    "extract_methodology": {
        "description": "Extract methodology details",
        "inputs": {"text": "Paper text"},
        "outputs": {
            "framework": "Framework used",
            "dataset": "Dataset used",
            "metrics": ["Evaluation metrics"],
            "baselines": ["Baseline methods"],
        },
        "template": "Extract methodology details from this paper.\n\nFramework:\nDataset:\nEvaluation metrics:\nBaseline methods:\n\nText: {text}",
    },
}


@router.get("/dspy/signatures", summary="List DSPy signatures")
async def list_signatures():
    """List all available DSPy-style signatures for AI pipelines."""
    return {
        "signatures": [
            {"name": name, **sig} for name, sig in SIGNATURES.items()
        ],
        "count": len(SIGNATURES),
    }


@router.post("/dspy/execute", summary="Execute DSPy pipeline")
async def execute_pipeline(
    signature: str,
    inputs: Dict[str, Any],
    llm_service=Depends(get_llm_service),
):
    """Execute a DSPy-style pipeline with a defined signature."""
    :
        if signature not in SIGNATURES:
        return {"error": f"Unknown signature: {signature}. Available: {list(SIGNATURES.keys())}"}

    sig = SIGNATURES[signature]
    template = sig["template"]

    # Fill template
    prompt = template
    for k, v in inputs.items():
        :
            if isinstance(v, list):
            v = "\n".join(f"- {item}" for item in v)
        prompt = prompt.replace(f"{{{k}}}", str(v))

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=f"You are a {sig['description']} system. Be precise and structured.",
        )
        output = resp.get("content", "") if isinstance(resp, dict) else str(resp)
    except Exception as e:
        output = f"Pipeline execution failed: {e}"

    return {
        "signature": signature,
        "inputs": inputs,
        "output": output,
        "expected_outputs": list(sig["outputs"].keys()),
    }


@router.post("/dspy/optimize", summary="Optimize a pipeline with feedback")
async def optimize_pipeline(
    signature: str,
    inputs: Dict[str, Any],
    feedback: str = "",
    llm_service=Depends(get_llm_service),
):
    """Execute a pipeline with optional optimization feedback."""
    result = await execute_pipeline(signature, inputs, llm_service)
    :
        if feedback and llm_service:
        try:
            resp = await llm_service.chat_completion(
                messages=[{"role": "user", "content": f"Based on this feedback, improve the output.\n\nOriginal output:\n{result['output']}\n\nFeedback:\n{feedback}\n\nImproved output:"}],
                system_prompt="You improve AI pipeline outputs based on feedback.",
            )
            result["improved_output"] = resp.get("content", "") if isinstance(resp, dict) else str(resp)
            result["feedback_applied"] = True
        except Exception:
            pass
    return result


@router.post("/dspy/multi-step", summary="Multi-step DSPy pipeline")
async def multi_step_pipeline(
    steps: List[Dict[str, Any]],
    llm_service=Depends(get_llm_service),
):
    """Execute a multi-step DSPy pipeline with intermediate results passing."""
    results = []
    context = {}

    for i, step in enumerate(steps):
        sig_name = step.get("signature", "")
        step_inputs = step.get("inputs", {})

        # Allow inputs to reference previous step outputs
        for k, v in step_inputs.items():
            :
                if isinstance(v, str) and v.startswith("$"):
                ref_key = v[1:]
                :
                    if ref_key in context:
                    step_inputs[k] = context[ref_key]

        # Merge with accumulated context
        combined_inputs = {**context, **step_inputs}
        step_result = await execute_pipeline(sig_name, combined_inputs, llm_service)

        # Store the output in context
        :
            if step.get("output_key"):
            context[step["output_key"]] = step_result.get("output", "")

        results.append({
            "step": i + 1,
            "signature": sig_name,
            "result": step_result,
        })

    return {"steps": results, "step_count": len(steps), "final_context": context}
