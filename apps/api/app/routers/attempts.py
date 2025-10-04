from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from ..db import engine
from ..schemas import AttemptIn

router = APIRouter()

@router.post("")
def register_attempt(body: AttemptIn):
    with engine.begin() as conn:
        q = conn.execute(text("SELECT correct_option FROM questions WHERE id::text = :id"), {"id": body.question_id}).fetchone()
        if not q:
            raise HTTPException(404, "Questão não encontrada")
        correct = (body.chosen_option.upper() == q.correct_option)
        row = conn.execute(text("""
          INSERT INTO attempts (question_id, chosen_option, correct)
          VALUES (:qid, :ch, :co) RETURNING id::text, question_id::text, chosen_option, correct, created_at
        """), {"qid": body.question_id, "ch": body.chosen_option.upper(), "co": correct}).mappings().first()
    return row

@router.get("/stats")
def stats():
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM attempts")).scalar() or 0
        correct = conn.execute(text("SELECT COUNT(*) FROM attempts WHERE correct")).scalar() or 0
        by_cat = conn.execute(text("""
          SELECT c.name as category, COUNT(a.*) as attempts,
                 SUM(CASE WHEN a.correct THEN 1 ELSE 0 END) as corrects,
                 ROUND( CASE WHEN COUNT(a.*)>0 THEN (SUM(CASE WHEN a.correct THEN 1 ELSE 0 END)::decimal / COUNT(a.*)) * 100 ELSE 0 END, 2) as accuracy_pct
          FROM attempts a
          JOIN questions q ON q.id = a.question_id
          LEFT JOIN categories c ON c.id = q.category_id
          GROUP BY c.name
          ORDER BY accuracy_pct DESC NULLS LAST
        """)).mappings().all()
    return {
        "total_attempts": total,
        "accuracy": round((correct / total * 100), 2) if total else 0,
        "by_category": by_cat
    }