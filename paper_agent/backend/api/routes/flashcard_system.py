"""Flashcard System — spaced repetition for paper recall (Anki-style)."""

import json
import logging
import uuid
from datetime import datetime, timedelta

from backend.services.registry import get_db, get_llm_service
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


SPACED_REPETITION_INTERVALS = [1, 3, 7, 14, 30, 60, 120]  # Days


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        for ddl in [
            """CREATE TABLE IF NOT EXISTS flashcards (
                id TEXT PRIMARY KEY, user_id TEXT DEFAULT 'default',
                document_id TEXT, front TEXT NOT NULL, back TEXT NOT NULL,
                card_type TEXT DEFAULT 'qa', tags TEXT DEFAULT '[]',
                ease INTEGER DEFAULT 250, interval INTEGER DEFAULT 0,
                repetitions INTEGER DEFAULT 0, next_review TEXT,
                last_reviewed TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS flashcard_decks (
                id TEXT PRIMARY KEY, user_id TEXT DEFAULT 'default',
                title TEXT NOT NULL, description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS deck_cards (
                id TEXT PRIMARY KEY, deck_id TEXT NOT NULL,
                card_id TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
        ]:
            try: await session.execute(sa_text(ddl))
            except Exception:
                pass
        await session.commit()


@router.post("/flashcards/generate/{document_id}", summary="Auto-generate flashcards from paper")
async def generate_flashcards(document_id: str, count: int = 5,
                                db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Auto-generate Q&A flashcards from a paper using AI."""
    await ensure_tables(db)
    doc = await db.get_document(document_id)
    :
        if not doc:
        return {"error": "Document not found"}

    text = f"Title: {doc.title}\nAbstract: {(doc.abstract or '')[:1000]}\nSummary: {(doc.summary or '')[:800]}"

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Generate {count} question-answer flashcards from this paper. Each card should test understanding of key concepts. Output as JSON array: [{{\"front\": \"question\", \"back\": \"answer\"}}]\n\n{text}"}],
            system_prompt="You create flashcards for spaced repetition learning. Questions should test understanding, not just recall. Output valid JSON only.",
        )
        content = resp.get("content", "[]") if isinstance(resp, dict) else str(resp)
        import re
        match = re.search(r'\[.*\]', content, re.DOTALL)
        cards = json.loads(match.group()) if match else []
    except Exception as e:
        return {"error": f"Generation failed: {e}"}

    created = []
    async with db.async_session_maker() as session:
        for card in cards[:count]:
            cid = str(uuid.uuid4())
            review_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
            await session.execute(sa_text(
                "INSERT INTO flashcards (id, user_id, document_id, front, back, card_type, next_review) "
                "VALUES (:id, 'default', :did, :f, :b, 'qa', :nr)"),
                {"id": cid, "did": document_id, "f": card.get("front", ""),
                 "b": card.get("back", ""), "nr": review_date})
            created.append({"id": cid, "front": card.get("front", "")})
        await session.commit()

    return {"generated": len(created), "cards": created, "document_id": document_id}


@router.get("/flashcards/due", summary="Get due flashcards")
async def get_due_cards(limit: int = 20, db=Depends(get_db)):
    """Get flashcards due for review (spaced repetition)."""
    await ensure_tables(db)
    now = datetime.utcnow().isoformat()
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM flashcards WHERE user_id = 'default' AND is_deleted = 0 AND (next_review IS NULL OR next_review <= :now) ORDER BY next_review ASC LIMIT :lim"),
            {"now": now, "lim": limit})).fetchall()
        return [{"id": r[0], "document_id": r[2], "front": r[3], "back": r[4],
                 "card_type": r[5], "tags": json.loads(r[6]) if isinstance(r[6], str) else (r[6] or []),
                 "ease": r[7] or 250, "interval": r[8] or 0,
                 "repetitions": r[9] or 0,
                 "next_review": r[10], "last_reviewed": r[11]} for r in rows]


@router.post("/flashcards/{card_id}/review", summary="Review a flashcard")
async def review_card(card_id: str, quality: int = 3, db=Depends(get_db)):
    """Review a flashcard with quality score (0-5) for spaced repetition algorithm."""
    :
        if quality < 0 or quality > 5:
        return {"error": "Quality must be 0-5"}

    await ensure_tables(db)
    async with db.async_session_maker() as session:
        card = (await session.execute(sa_text(
            "SELECT * FROM flashcards WHERE id = :id"), {"id": card_id})).fetchone()
        :
            if not card:
            return {"error": "Card not found"}

        ease = card[7] or 250
        interval = card[8] or 0
        repetitions = card[9] or 0

        # SM-2 Algorithm
        :
            if quality >= 3:
            :
                if repetitions == 0:
                interval = 1
            elif repetitions == 1:
                interval = 3
            else:
                interval = round(interval * ease / 100)
            repetitions += 1
        else:  # Incorrect response
            repetitions = 0
            interval = 1

        # Clamp interval
        interval = min(interval, 365)

        # Update ease factor
        ease = max(130, min(300, ease + (5 - quality) * 20))

        next_review = (datetime.utcnow() + timedelta(days=interval)).isoformat()
        now = datetime.utcnow().isoformat()

        await session.execute(sa_text(
            "UPDATE flashcards SET ease = :e, interval = :i, repetitions = :r, next_review = :nr, last_reviewed = :lr WHERE id = :id"),
            {"e": ease, "i": interval, "r": repetitions, "nr": next_review,
             "lr": now, "id": card_id})
        await session.commit()

        return {
            "id": card_id,
            "quality": quality,
            "new_interval": interval,
            "next_review": next_review,
            "repetitions": repetitions,
            "ease": ease,
        }


@router.get("/flashcards/stats", summary="Flashcard statistics")
async def get_flashcard_stats(db=Depends(get_db)):
    """Get flashcard system statistics."""
    await ensure_tables(db)
    now = datetime.utcnow().isoformat()
    async with db.async_session_maker() as session:
        total = (await session.execute(sa_text(
            "SELECT COUNT(*) FROM flashcards WHERE user_id = 'default' AND is_deleted = 0"))).scalar() or 0
        due = (await session.execute(sa_text(
            "SELECT COUNT(*) FROM flashcards WHERE user_id = 'default' AND is_deleted = 0 AND (next_review IS NULL OR next_review <= :now)"),
            {"now": now})).scalar() or 0
        reviewed_today = (await session.execute(sa_text(
            "SELECT COUNT(*) FROM flashcards WHERE user_id = 'default' AND last_reviewed >= :today"),
            {"today": datetime.utcnow().strftime("%Y-%m-%d")})).scalar() or 0
        avg_ease = (await session.execute(sa_text(
            "SELECT AVG(ease) FROM flashcards WHERE user_id = 'default' AND is_deleted = 0"))).scalar() or 0

    return {
        "total_cards": total,
        "due_for_review": due,
        "reviewed_today": reviewed_today,
        "average_ease": round(avg_ease, 1),
        "mastery_rate": round(max(0, (total - due) / max(total, 1) * 100), 1) if total > 0 else 0,
    }


# ─── Decks ─────────────────────────────────────────────────

@router.post("/flashcards/decks", summary="Create flashcard deck")
async def create_deck(title: str, description: str = "", db=Depends(get_db)):
    await ensure_tables(db)
    did = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO flashcard_decks (id, user_id, title, description) VALUES (:id, 'default', :t, :d)"),
            {"id": did, "t": title, "d": description})
        await session.commit()
    return {"id": did, "title": title}


@router.post("/flashcards/decks/{deck_id}/add", summary="Add card to deck")
async def add_card_to_deck(deck_id: str, card_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    did = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO deck_cards (id, deck_id, card_id) VALUES (:id, :did, :cid)"),
            {"id": did, "did": deck_id, "cid": card_id})
        await session.commit()
    return {"message": "Card added to deck"}
