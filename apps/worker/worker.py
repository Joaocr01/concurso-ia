import os, ast, json, time, hashlib, datetime, math
from redis import Redis
import psycopg
from psycopg.rows import dict_row
from pypdf import PdfReader
import io
import random

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")

try:
    if OPENAI_API_KEY:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    else:
        openai_client = None
except Exception:
    openai_client = None

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL")

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "generate_questions.pt-BR.txt")

def read_prompt():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()

def extract_pdf_text(raw_bytes: bytes):
    reader = PdfReader(io.BytesIO(raw_bytes))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        txt = page.extract_text() or ""
        pages.append((i, txt))
    return pages

def segment_text(text: str):
    # simples: separa por parágrafos duplos ou ~1200 chars
    raw_blocks = [p.strip() for p in text.split("\n\n") if p.strip()]
    blocks = []
    for idx, blk in enumerate(raw_blocks, start=1):
        blocks.append({"location": f"bloco {idx}", "content": blk})
    return blocks

def hash_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def embed(text: str):
    if openai_client:
        # Real embedding
        try:
            resp = openai_client.embeddings.create(
                input=text,
                model=EMBED_MODEL
            )
            return resp.data[0].embedding
        except Exception:
            pass
    # fallback pseudo embedding
    random.seed(hash_text(text)[:16])
    return [random.uniform(-0.5, 0.5) for _ in range(32)]

def cosine(a, b):
    if not a or not b: return 0.0
    if len(a) != len(b):
        # adjust length (fallback)
        m = min(len(a), len(b))
        a, b = a[:m], b[:m]
    dot = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(x*x for x in b))
    if na == 0 or nb == 0: return 0.0
    return dot / (na * nb)

def llm_generate(block_content: str, filename: str):
    # Placeholder lógico: cria 1 questão simples se houver mais de 40 chars
    now = datetime.datetime.now().astimezone().isoformat()
    if len(block_content) < 40:
        return {"questions": [], "skipped": [{"source_block": "short", "skipped_reason": "bloco muito curto"}]}
    base_hash = hash_text(block_content)[:24]
    qid = f"q_{base_hash}"
    # Simples heurística de enunciado
    enun = "Com base no trecho apresentado, qual afirmação reflete corretamente o conteúdo central?"
    quest = {
      "id": qid,
      "source_file": filename,
      "source_location": "bloco 1",
      "category_id": None,
      "category_name": "Categoria Geral",
      "auto_created_category": True,
      "title": "Ideia central do trecho",
      "enunciado": enun,
      "alternatives": {
        "A": "Uma conclusão que não aparece no texto",
        "B": "Um detalhe secundário irrelevante",
        "C": "A ideia principal explicitada no trecho",
        "D": "Uma contradição direta ao texto",
        "E": "Um dado estatístico inexistente"
      },
      "correct_option": "C",
      "justification": "A alternativa C corresponde ao núcleo temático do bloco (linha inicial).",
      "difficulty": 2,
      "estimated_time_seconds": 60,
      "tags": ["gerado", "ideia-central"],
      "embedding": "EMBEDDING_PLACEHOLDER",
      "confidence": 0.72,
      "duplicate": False,
      "possible_duplicate_of": None,
      "needs_review": False,
      "created_by": "system_generated",
      "created_at": now,
      "hash": hash_text(block_content)[:56],
      "notes": "",
      "edit_suggestions": ["Verificar se o enunciado pode citar a linha exata do bloco."]
    }
    return {"questions": [quest], "skipped": []}

def ensure_category(conn, name: str):
    cur = conn.execute("SELECT id::text, name FROM categories WHERE name=%s", (name,))
    row = cur.fetchone()
    if row:
        return row["id"], False
    cur = conn.execute(
        "INSERT INTO categories (name, description, auto_created) VALUES (%s,%s,true) RETURNING id::text",
        (name, "Auto criada").
    )
    return cur.fetchone()["id"], True

def fetch_existing_question_embeddings(conn):
    cur = conn.execute("SELECT id::text, embedding FROM questions WHERE embedding IS NOT NULL")
    existing = []
    for r in cur:
        emb = r["embedding"]
        existing.append((r["id"], emb))
    return existing

def save_embedding(conn, question_id, vector):
    # usa SQL direto
    if vector and openai_client:
        # adapt to dimension
        dims = len(vector)
    conn.execute("UPDATE questions SET embedding=%s WHERE id=%s", (vector, question_id,))

def similarity_category(conn, q_emb):
    cur = conn.execute("SELECT id::text, name, embedding FROM categories LEFT JOIN category_embeddings ce ON ce.category_id = categories.id")
    best_id = None
    best_sim = 0
    rows = cur.fetchall()
    for r in rows:
        emb = r["embedding"]
        if emb is None: continue
        sim = cosine(emb, q_emb)
        if sim > best_sim:
            best_sim = sim
            best_id = r["id"]
    return best_id, best_sim

def upsert_category_embedding(conn, category_id, emb):
    cur = conn.execute("SELECT category_id FROM category_embeddings WHERE category_id=%s", (category_id,))
    if cur.fetchone():
        return
    conn.execute("INSERT INTO category_embeddings (category_id, embedding) VALUES (%s,%s)", (category_id, emb))

def detect_duplicates(existing, new_emb):
    # existing: list of (id, embedding)
    best = []
    for eid, emb in existing:
        sim = cosine(emb, new_emb)
        best.append((eid, sim))
    best.sort(key=lambda x: x[1], reverse=True)
    if not best:
        return None, None
    top_id, top_sim = best[0]
    if top_sim >= 0.92:
        return ("duplicate", top_id)
    if 0.85 <= top_sim < 0.92:
        return ("possible", top_id)
    return (None, None)

def persist_question(conn, q):
    conn.execute("""
      INSERT INTO questions (id, source_file, source_location, category_id, auto_created_category, title, enunciado,
        alternatives, correct_option, justification, difficulty, estimated_time_seconds, tags, embedding, confidence,
        duplicate, possible_duplicate_of, needs_review, created_by, created_at, hash, notes)
      VALUES (%s,%s,%s,%s,%s,%s,%s,
              %s,%s,%s,%s,%s,%s,NULL,%s,
              %s,%s,%s,%s,%s,%s,%s)
      ON CONFLICT (id) DO NOTHING
    """, (
        q["id"], q.get("source_file"), q.get("source_location"), q.get("category_id"),
        q.get("auto_created_category", False), q.get("title"), q["enunciado"],
        json.dumps(q["alternatives"]), q["correct_option"], q.get("justification"),
        q.get("difficulty", 2), q.get("estimated_time_seconds", 60),
        json.dumps(q.get("tags", [])),
        q.get("confidence", 0.7),
        q.get("duplicate", False), q.get("possible_duplicate_of"),
        q.get("needs_review", False), q.get("created_by", "system_generated"),
        q.get("created_at"), q.get("hash"), q.get("notes", "")
    ))

def process_block(conn, block, filename):
    generation = llm_generate(block["content"], filename)
    existing_embeddings = fetch_existing_question_embeddings(conn)
    for q in generation["questions"]:
        # embedding
        q_emb = embed(q["enunciado"] + " " + q["justification"])
        # categorizar
        cat_name = q.get("category_name") or "Geral"
        cat_id, created = ensure_category(conn, cat_name)
        q["category_id"] = cat_id
        q["auto_created_category"] = created
        # duplicidade
        status, ref_id = detect_duplicates(existing_embeddings, q_emb)
        if status == "duplicate":
            q["duplicate"] = True
            q["possible_duplicate_of"] = ref_id
        elif status == "possible":
            q["needs_review"] = True
            q["possible_duplicate_of"] = ref_id
        # persistir
        persist_question(conn, q)
        # salvar embedding
        save_embedding(conn, q["id"], q_emb)
    return generation

def main():
    r = Redis.from_url(REDIS_URL)
    print("Worker rodando...")
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()
        while True:
            item = r.brpop("ingest_queue", timeout=5)
            if not item:
                continue
            try:
                job = ast.literal_eval(item[1].decode("utf-8"))
                filename = job.get("filename", "input")
                print(f"Job recebido: {filename}")
                if job["type"] == "text":
                    blocks = segment_text(job["content"])
                else:
                    raw_bytes = job.get("raw_bytes")
                    if raw_bytes:
                        pages = extract_pdf_text(raw_bytes)
                        joined = "\n\n".join(p[1] for p in pages if p[1].strip())
                        blocks = segment_text(joined)
                    else:
                        blocks = segment_text(job.get("content") or "")
                with conn.transaction():
                    for b in blocks:
                        process_block(conn, b, filename)
            except Exception as e:
                print("Erro no worker:", e)
            time.sleep(0.1)

if __name__ == "__main__":
    main()