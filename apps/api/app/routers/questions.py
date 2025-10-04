from fastapi import APIRouter, Query
from sqlalchemy import text
from ..db import engine

router = APIRouter()

@router.get("")
def list_questions(category_id: str | None = Query(default=None), limit: int = 50, offset: int = 0):
    where = ""
    params = {"limit": limit, "offset": offset}
    if category_id:
        where = "WHERE category_id = :category_id"
        params["category_id"] = category_id
    sql = text(f"""
      SELECT q.id::text, q.source_file, q.source_location, q.category_id::text, 
             q.auto_created_category, q.title, q.enunciado,
             q.alternatives, q.correct_option, q.justification, q.difficulty,
             q.estimated_time_seconds, COALESCE(q.tags, '[]'::json) as tags,
             COALESCE(q.confidence,0.7) as confidence, q.duplicate, q.possible_duplicate_of::text, q.needs_review,
             COALESCE(q.created_by, 'system_generated') as created_by, q.created_at, q.hash, COALESCE(q.notes,'') as notes,
             c.name as category_name
      FROM questions q
      LEFT JOIN categories c ON c.id = q.category_id
      {where}
      ORDER BY q.created_at DESC
      LIMIT :limit OFFSET :offset
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    for row in rows:
        row["embedding"] = "EMBEDDING_PLACEHOLDER"
    return {"questions": rows, "skipped": []}