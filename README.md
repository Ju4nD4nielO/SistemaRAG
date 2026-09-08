


## Infraestructura (PostgreSQL + pgvector)

### 1. Levantar el contenedor

```bash
docker compose up -d
```

(o `podman-compose up -d` si usan Podman)

Esto levanta Postgres 16 con la extensión `pgvector` ya instalada
(imagen `pgvector/pgvector:pg16`) y corre automáticamente `init.sql`
la primera vez, creando la extensión `vector` y la tabla `faqs`.

> Si ya tenían un contenedor de Postgres corriendo de antes (volumen
> ya inicializado), `init.sql` no se vuelve a ejecutar solo. En ese
> caso corran a mano:
> ```bash
> docker exec -i parachute_pgvector psql -U parachute -d parachute_faqs < init.sql
> ```

### 2. Configurar variables de entorno

Copien `.env.example` a `.env` y ajusten si es necesario (los valores
por defecto ya coinciden con `docker-compose.yml`):

```bash
cp .env.example .env
```

### 3. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

### 4. Cargar los FAQs a la base de datos

```bash
python load_faqs.py Corpus_FAQs_Parachute_SA_2026.txt
```

El script:
1. Parsea el corpus (120 FAQs, delimitadas por bloques `ID:` / `CATEGORÍA:` / `PREGUNTA:` / `RESPUESTA:` / `METADATA:`).
2. Genera un embedding de 384 dimensiones por FAQ con `sentence-transformers` (`all-MiniLM-L6-v2`), sobre el texto de la pregunta + respuesta.
3. Hace un `UPSERT` a la tabla `faqs` en Postgres (se puede correr varias veces sin duplicar filas).

Para confirmar que cargó bien:

```bash
docker exec -it parachute_pgvector psql -U parachute -d parachute_faqs -c "SELECT count(*) FROM faqs;"
```

Debería devolver `120`.

### Esquema de la tabla

```sql
faqs (
    id          TEXT PRIMARY KEY,   -- "FAQ-001", "FAQ-002", ...
    categoria   TEXT NOT NULL,
    pregunta    TEXT NOT NULL,
    respuesta   TEXT NOT NULL,
    metadata    JSONB,
    embedding   VECTOR(384) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
)
```

Índice `ivfflat` sobre `embedding` con distancia coseno, listo para que
el agente (Persona 2) haga consultas del estilo:

```sql
SELECT id, categoria, pregunta, respuesta
FROM faqs
ORDER BY embedding <=> %s::vector
LIMIT 3;
```