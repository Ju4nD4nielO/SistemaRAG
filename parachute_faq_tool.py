"""Herramienta de consulta para la base de conocimiento de Parachute S.A."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

from parachute_vector_store import (
    EMBEDDING_MODEL_NAME,
    connect_to_faq_store,
    to_pgvector_literal,
)

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


DEFAULT_RESULT_COUNT = 5
MAX_RESULT_COUNT = 10

FAQ_SEARCH_SQL = """
    SELECT
        id,
        categoria,
        pregunta,
        respuesta,
        embedding <=> %s::vector AS distancia_coseno
    FROM faqs
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
"""

BUSCAR_FAQ_TOOL = {
    "type": "function",
    "function": {
        "name": "buscar_faq",
        "description": (
            "Úsala antes de responder cualquier pregunta sobre los servicios, "
            "políticas o información de Parachute S.A. Busca exclusivamente en "
            "la base oficial de FAQs y devuelve las entradas más relacionadas. "
            "No debe utilizarse como fuente de conocimiento general."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pregunta": {
                    "type": "string",
                    "description": (
                        "Pregunta o necesidad del usuario expresada en español."
                    ),
                },
                "k": {
                    "type": "integer",
                    "description": "Cantidad de FAQs candidatas que se deben recuperar.",
                    "default": DEFAULT_RESULT_COUNT,
                    "minimum": 1,
                    "maximum": MAX_RESULT_COUNT,
                },
            },
            "required": ["pregunta"],
            "additionalProperties": False,
        },
    },
}


@lru_cache(maxsize=1)
def _get_embedding_model() -> SentenceTransformer:
    """Carga una sola vez el mismo modelo utilizado al poblar la tabla."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def _validate_search(pregunta: str, k: int) -> tuple[str, int]:
    if not isinstance(pregunta, str) or not pregunta.strip():
        raise ValueError("La pregunta debe contener texto.")

    if isinstance(k, bool) or not isinstance(k, int):
        raise ValueError("La cantidad de resultados debe ser un número entero.")

    if not 1 <= k <= MAX_RESULT_COUNT:
        raise ValueError(
            f"La cantidad de resultados debe estar entre 1 y {MAX_RESULT_COUNT}."
        )

    return pregunta.strip(), k


def _embed_question(pregunta: str) -> str:
    embedding = _get_embedding_model().encode(
        pregunta,
        normalize_embeddings=True,
    )
    return to_pgvector_literal(embedding)


def buscar_faq(
    pregunta: str,
    k: int = DEFAULT_RESULT_COUNT,
) -> dict[str, Any]:
    """Recupera las FAQs más cercanas a ``pregunta`` mediante distancia coseno."""
    pregunta, k = _validate_search(pregunta, k)
    query_vector = _embed_question(pregunta)

    connection = connect_to_faq_store()
    try:
        with connection.cursor() as cursor:
            cursor.execute(FAQ_SEARCH_SQL, (query_vector, query_vector, k))
            rows = cursor.fetchall()
    finally:
        connection.close()

    resultados = [
        {
            "id": faq_id,
            "categoria": categoria,
            "pregunta": pregunta_faq,
            "respuesta": respuesta,
            "distancia_coseno": round(float(distancia), 6),
        }
        for faq_id, categoria, pregunta_faq, respuesta, distancia in rows
    ]

    return {
        "consulta": pregunta,
        "cantidad": len(resultados),
        "resultados": resultados,
    }