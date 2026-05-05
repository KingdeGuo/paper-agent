"""First-Run Wizard — onboarding experience for new users."""

import logging
import uuid
from datetime import datetime

from backend.services.registry import get_db
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


ONBOARDING_STEPS = [
    {"id": "welcome", "title": "Welcome to Paper Agent!", "description": "Your AI Research Companion", "required": False},
    {"id": "upload_first_paper", "title": "Upload Your First Paper", "description": "Import a PDF, paste a DOI, or search arXiv", "required": True},
    {"id": "configure_llm", "title": "Configure AI", "description": "Set up an LLM provider for AI summaries and analysis", "required": False},
    {"id": "create_folder", "title": "Organize Your Library", "description": "Create a literature tree folder structure", "required": False},
    {"id": "set_goals", "title": "Set Reading Goals", "description": "Define your weekly reading targets", "required": False},
    {"id": "connect_zotero", "title": "Import from Zotero", "description": "Sync your existing Zotero library", "required": False},
    {"id": "explore_features", "title": "Explore Features", "description": "Take a tour of what Paper Agent can do", "required": False},
]


@router.get("/onboarding/status", summary="Get onboarding status")
async def get_onboarding_status(db=Depends(get_db)):
    """Get the current user's onboarding progress."""
    has_docs = False
    has_llm = False
    has_folders = False
    has_goals = False
    has_zotero = False

    # Check if user has documents
    try:
        docs = await db.get_documents(limit=1) if db else []
        has_docs = len(docs) > 0
    except Exception:
        pass

    # Check if LLM is configured
    try:
        from backend.services.registry import get_llm_service
        llm = get_llm_service()
        has_llm = llm is not None and hasattr(llm, 'provider') and llm.provider is not None
    except Exception:
        pass

    # Check if literature tree has nodes
    try:
        async with db.async_session_maker() as session:
            cnt = (await session.execute(sa_text("SELECT COUNT(*) FROM directory_nodes WHERE is_deleted = 0"))).scalar() or 0
            has_folders = cnt > 0
    except Exception:
        pass

    # Check if reading goals exist
    try:
        async with db.async_session_maker() as session:
            cnt = (await session.execute(sa_text("SELECT COUNT(*) FROM reading_goals WHERE is_active = 1"))).scalar() or 0
            has_goals = cnt > 0
    except Exception:
        pass

    # Check Zotero connected
    try:
        async with db.async_session_maker() as session:
            cnt = (await session.execute(sa_text("SELECT COUNT(*) FROM zotero_credentials"))).scalar() or 0
            has_zotero = cnt > 0
    except Exception:
        pass

    # Determine completed steps
    completed_steps = ["welcome"]
    :
        if has_docs:
    :
        if has_llm:
    :
        if has_folders:
    :
        if has_goals:
    :
        if has_zotero:

    # Determine overall progress
    required_steps = [s for s in ONBOARDING_STEPS if s["required"]]
    completed_required = [s for s in required_steps if s["id"] in completed_steps]
    progress = round(len(completed_steps) / len(ONBOARDING_STEPS) * 100)
    required_progress = round(len(completed_required) / max(len(required_steps), 1) * 100)

    return {
        "in_progress": progress < 100,
        "progress": progress,
        "required_progress": required_progress,
        "completed_steps": completed_steps,
        "next_step": _get_next_step(completed_steps),
        "steps": [
            {**s, "completed": s["id"] in completed_steps}
            for s in ONBOARDING_STEPS
        ],
    }


def _get_next_step(completed):
    for step in ONBOARDING_STEPS:
        :
            if step["id"] not in completed:
            return step
    return None


@router.post("/onboarding/complete/{step_id}", summary="Mark step as complete")
async def complete_step(step_id: str, db=Depends(get_db)):
    """Mark an onboarding step as completed."""
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT OR IGNORE INTO onboarding_progress (id, user_id, step_id, completed_at) "
            "VALUES (:id, 'default', :sid, :n)"),
            {"id": str(uuid.uuid4()), "sid": step_id, "n": datetime.utcnow().isoformat()})
        await session.commit()
    return {"step": step_id, "completed": True}


@router.get("/onboarding/demo-data", summary="Load demo data")
async def load_demo_data(db=Depends(get_db)):
    """Load example papers and data for demonstration."""
    imported = 0
    demo_papers = [
        {
            "title": "Attention Is All You Need",
            "authors": ["Vaswani, Ashish", "Shazeer, Noam", "Parmar, Niki"],
            "year": 2017, "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
        },
        {
            "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            "authors": ["Devlin, Jacob", "Chang, Ming-Wei", "Lee, Kenton"],
            "year": 2019, "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers.",
        },
        {
            "title": "Deep Residual Learning for Image Recognition",
            "authors": ["He, Kaiming", "Zhang, Xiangyu", "Ren, Shaoqing"],
            "year": 2016, "abstract": "Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions.",
        },
        {
            "title": "Generative Adversarial Networks",
            "authors": ["Goodfellow, Ian", "Pouget-Abadie, Jean", "Mirza, Mehdi"],
            "year": 2014, "abstract": "We propose a new framework for estimating generative models via an adversarial process, in which we simultaneously train two models: a generative model G that captures the data distribution, and a discriminative model D that estimates the probability that a sample came from the training data rather than G.",
        },
        {
            "title": "Learning Transferable Visual Models From Natural Language Supervision",
            "authors": ["Radford, Alec", "Kim, Jong Wook", "Hallacy, Chris"],
            "year": 2021, "abstract": "We demonstrate that the simple pre-training task of predicting which caption goes with which image is an efficient and scalable way to learn SOTA image representations from scratch on a dataset of 400 million (image, text) pairs collected from the internet.",
        },
    ]

    for paper in demo_papers:
        try:
            doc = await db.create_document({
                "filename": f"demo_{paper['title'][:20].replace(' ', '_')}.pdf",
                "title": paper["title"], "authors": paper["authors"],
                "year": paper["year"], "abstract": paper["abstract"],
                "file_path": "", "file_size": 0, "processed": 0,
                "keywords": paper["title"].lower().split()[:5],
            })
            imported += 1
        except Exception as e:
            logger.warning(f"Demo import failed: {e}")

    return {"imported": imported, "message": f"Loaded {imported} demo papers into your library. Explore the features!"}
