
# Sistema RAG de FAQs — Parachute S.A.

Agente de terminal que responde únicamente con información recuperada del
corpus oficial `Corpus_FAQs_Parachute_SA_2026.txt`. Los embeddings se almacenan
en PostgreSQL con pgvector y el modelo consulta la base mediante function
calling real con el SDK compatible con OpenAI de Groq.

## Infraestructura (PostgreSQL + pgvector)

### 1. Levantar el contenedor

```bash
docker compose up -d
```

(o `podman-compose up -d` si usan Podman)

Esto levanta Postgres 16 con la extensión `pgvector` ya instalada
(imagen `pgvector/pgvector:pg16`) y corre automáticamente `init.sql`
la primera vez, creando la extensión `vector` y la tabla `faqs`.

Comprueben que el servicio está saludable antes de cargar el corpus:

```bash
docker compose ps
```

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

Además de las credenciales de PostgreSQL, agreguen una clave válida de Groq:

```dotenv
GROQ_API_KEY=tu_api_key_de_groq
# Opcional; por defecto se usa openai/gpt-oss-20b
GROQ_MODEL=openai/gpt-oss-20b
# Opcional; distancia coseno máxima que se considera evidencia válida
FAQ_MAX_COSINE_DISTANCE=0.65
```

`FAQ_MAX_COSINE_DISTANCE` es una defensa contra preguntas ajenas al corpus: una
búsqueda vectorial siempre devuelve vecinos, pero solo se envían al agente los
que están por debajo de ese umbral. Si cambian de modelo o corpus, calibren el
valor con las preguntas de validación incluidas más abajo.

### 3. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

La primera ejecución de `sentence-transformers` puede descargar el modelo
multilingüe `paraphrase-multilingual-MiniLM-L12-v2`; por eso requiere conexión
a internet una sola vez, salvo que el modelo ya esté en caché.

### 4. Cargar los FAQs a la base de datos

```bash
python load_faqs.py Corpus_FAQs_Parachute_SA_2026.txt
```

Si ya habían cargado la base con una versión anterior del proyecto, ejecuten
este comando nuevamente: el UPSERT reemplaza los embeddings existentes por los
del modelo multilingüe y no duplica filas.

El script:
1. Parsea el corpus (120 FAQs, delimitadas por bloques `ID:` / `CATEGORÍA:` / `PREGUNTA:` / `RESPUESTA:` / `METADATA:`).
2. Genera un embedding de 384 dimensiones por FAQ con `sentence-transformers`
   (`paraphrase-multilingual-MiniLM-L12-v2`) a partir de la pregunta. Se eligió
   este modelo multilingüe porque las consultas y el corpus están en español;
   evita que las respuestas repetitivas del dump distorsionen la búsqueda.
3. Hace un `UPSERT` a la tabla `faqs` en Postgres (se puede correr varias veces sin duplicar filas).

Para confirmar que cargó bien:

```bash
docker exec -it parachute_pgvector psql -U parachute -d parachute_faqs -c "SELECT count(*) FROM faqs;"
```

Debería devolver `120`.

### 5. Ejecutar el agente

```bash
python main.py
```

El agente conserva una sesión interactiva: escriban `Bye` o usen `Ctrl-C` para
salir. Por cada pregunta imprime una línea `[Herramienta] buscar_faq` con los
IDs recuperados; esa traza permite verificar que consulta PostgreSQL antes de
producir la respuesta.

El flujo es el siguiente:

```text
pregunta → modelo solicita buscar_faq → pgvector recupera evidencia
         → resultado con rol tool → modelo redacta usando solo esa evidencia
```

Si ninguna coincidencia supera el umbral de relevancia, el programa devuelve:

> Lo siento, no puedo responder esa pregunta porque no está contemplada en la información disponible de Parachute S.A.

No se incluye el archivo completo en el prompt ni se usa el archivo legado
`FAQs_Parachute_SA_Guatemala_2026.txt` como fuente del agente.

### Pruebas

Las pruebas no requieren Docker, modelo descargado ni una API key:

```bash
python -m unittest discover -s tests -v
```

Cubren el parser del corpus, la validación de la herramienta y el intercambio
de mensajes de function calling, incluido el rechazo cuando no hay evidencia.

### Preguntas de validación

- “¿Cómo llego desde la Ciudad de Guatemala al aeródromo?” (logística).
- “¿Cuál es el límite de peso para realizar el salto?” (requisitos físicos).
- “¿Qué métodos de pago aceptan?” (precios y pagos).
- “¿Puedo llevar mi propia cámara durante el salto?” (multimedia).
- “¿Qué sucede si el clima no permite realizar el salto?” (contingencias).
- “¿Cuál es la capital de Francia?” (debe rechazarla).

Para una pregunta con varias partes, prueben: “¿Cuál es el límite de peso y qué
ocurre si hay mal clima?”. El agente debe limitarse a la evidencia recuperada.

## Video de demostración

Para ver el video de prueba haz click [aquí](https://youtu.be/vTC4lDADHNc)
