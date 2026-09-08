-- Se ejecuta automáticamente la primera vez que se crea el volumen del contenedor
-- (docker-entrypoint-initdb.d). Si ya tenías el contenedor levantado antes de
-- agregar este archivo, corre este script a mano una vez (ver README).

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS faqs (
    id          TEXT PRIMARY KEY,        -- p.ej. "FAQ-001"
    categoria   TEXT NOT NULL,
    pregunta    TEXT NOT NULL,
    respuesta   TEXT NOT NULL,
    metadata    JSONB,
    embedding   VECTOR(384) NOT NULL,    -- 384 dims = all-MiniLM-L6-v2
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice para búsquedas de similitud por coseno (ivfflat).
-- lists=100 es razonable para corpus de hasta unos miles de filas;
-- con 120 FAQs igual funciona un exact scan, pero dejamos el índice listo.
CREATE INDEX IF NOT EXISTS faqs_embedding_idx
    ON faqs
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS faqs_categoria_idx ON faqs (categoria);