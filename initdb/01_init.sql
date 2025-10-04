CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE,
  name TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user_id UUID REFERENCES users(id),
  filename TEXT,
  storage_key TEXT,
  pages_count INT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS blocks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
  page INT,
  location TEXT,
  content TEXT NOT NULL,
  hash TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  auto_created BOOLEAN DEFAULT false,
  parent_id UUID REFERENCES categories(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS category_embeddings (
  category_id UUID PRIMARY KEY REFERENCES categories(id) ON DELETE CASCADE,
  embedding vector(3072) -- se usar text-embedding-3-large
);

CREATE TABLE IF NOT EXISTS questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_file TEXT,
  source_location TEXT,
  category_id UUID REFERENCES categories(id),
  auto_created_category BOOLEAN DEFAULT false,
  title TEXT,
  enunciado TEXT NOT NULL,
  alternatives JSONB NOT NULL,
  correct_option CHAR(1) NOT NULL,
  justification TEXT,
  difficulty INT,
  estimated_time_seconds INT,
  tags JSONB,
  embedding vector(3072),
  confidence DOUBLE PRECISION,
  duplicate BOOLEAN DEFAULT false,
  possible_duplicate_of UUID REFERENCES questions(id),
  needs_review BOOLEAN DEFAULT false,
  created_by TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  hash TEXT UNIQUE,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  chosen_option CHAR(1),
  correct BOOLEAN,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
  status TEXT CHECK (status IN ('pending','approved','rejected')) DEFAULT 'pending',
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category_id);
CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts(user_id);