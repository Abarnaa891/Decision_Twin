-- PostgreSQL logical schema. SQLAlchemy creates the starter tables on API startup.
CREATE TABLE IF NOT EXISTS datasets (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  industry VARCHAR(50) NOT NULL,
  filename VARCHAR(255) NOT NULL,
  row_count INTEGER NOT NULL DEFAULT 0,
  column_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS simulations (
  id VARCHAR(36) PRIMARY KEY,
  dataset_id VARCHAR(36) NOT NULL REFERENCES datasets(id),
  industry VARCHAR(50) NOT NULL,
  inputs JSONB NOT NULL,
  outputs JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
