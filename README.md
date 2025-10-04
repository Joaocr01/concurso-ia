# Concurse AI — Plataforma de Questões de Concurso com Geração por PDF/Texto

Este repositório implementa uma plataforma que:
1. Faz upload de PDF ou texto
2. Segmenta em blocos
3. Gera questões de múltipla escolha (A–E) com base no texto
4. Classifica em categorias (cria novas se necessário)
5. Detecta duplicatas / possíveis duplicatas
6. Permite responder questões e gera estatísticas

## Stack
- Frontend: Next.js
- Backend: FastAPI
- Worker: Python (Redis queue)
- Banco: Postgres + pgvector
- Cache/Fila: Redis
- Armazenamento: MinIO (S3 compatível)
- IA: OpenAI (opcional) — fallback placeholder

## Melhorias Incluídas
- Extração de PDF (pypdf)
- Embeddings (OpenAI) ou placeholder
- Endpoint de tentativas: POST /attempts
- Estatísticas: GET /attempts/stats
- Algoritmo simples de similaridade (cosine embeddings ou bag-of-words)
- Marcação fields: duplicate, possible_duplicate_of, needs_review

## Rodar (Desenvolvimento)
```bash
cp .env.example .env
docker compose up --build
```

Serviços:
- API: http://localhost:8000/docs
- Web: http://localhost:3000
- MinIO: http://localhost:9001 (minio / minio123)

## Fluxo
1. Upload (POST /upload ou via UI /upload)
2. Worker processa fila ingest_queue
3. Gera questões e salva no banco
4. Listagem em /questions ou via UI /dashboard
5. Responder questões: POST /attempts
6. Estatísticas: GET /attempts/stats

## Embeddings
- Setar OPENAI_API_KEY para ativar embeddings reais (modelo: text-embedding-3-large por padrão).
- Caso contrário, usa vetor placeholder com ruído.

## Duplicatas / Similaridade
- Se cosine >= 0.92 → duplicate
- 0.85–0.92 → possible_duplicate
- Categorias:
  - >=0.80 mesma categoria
  - 0.60–0.80 needs_review
  - <0.60 cria nova

## Próximos Passos Sugeridos
- Autenticação (NextAuth + JWT)
- UI de resposta por questão (marcar feedback imediato)
- Revisão manual (approve/reject)
- Fusão de categorias
- Spaced repetition / algoritmo de reforço
- Testes automatizados (pytest + playwright)

## Script para gerar ZIP
```bash
bash scripts/build_zip.sh
```

## Licença
MIT