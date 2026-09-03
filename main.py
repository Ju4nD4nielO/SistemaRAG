import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent
FAQ_FILE = BASE_DIR / "FAQs_Parachute_SA_Guatemala_2026.txt"

SYSTEM_PROMPT = """
Eres el agente de preguntas frecuentes de Parachute S.A.

REGLAS OBLIGATORIAS:
1. Responde EXCLUSIVAMENTE usando la información contenida en el documento
   de preguntas frecuentes proporcionado como contexto.
2. No uses conocimiento general, internet, suposiciones ni información que no
   aparezca explícitamente en el documento.
3. Si la pregunta no puede responderse con el documento, responde exactamente:
   "Lo siento, no puedo responder esa pregunta porque no está contemplada
   en la información disponible de Parachute S.A."
4. Si la pregunta contiene varias partes, responde únicamente las partes que
   sí estén respaldadas por el documento y señala cuáles no están contempladas.
5. No inventes precios, horarios, políticas, ubicaciones, teléfonos, correos
   ni ningún otro dato.
6. Responde en español, de forma clara y concisa.
"""


def load_faq() -> str:
    """Carga el documento que funciona como nuestra base de conocimiento."""
    if not FAQ_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de FAQs: {FAQ_FILE}"
        )

    return FAQ_FILE.read_text(encoding="utf-8")


def create_client() -> OpenAI:
    """Crea un cliente OpenAI-compatible apuntando a Groq."""
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "No se encontró GROQ_API_KEY. "
            "Crea un archivo .env con tu API Key de Groq."
        )

    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )


def answer_question(client: OpenAI, faq_context: str, question: str) -> str:
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    "DOCUMENTO OFICIAL DE FAQs:\n\n"
                    f"{faq_context}\n\n"
                    "PREGUNTA DEL USUARIO:\n"
                    f"{question}"
                ),
            },
        ],
    )

    return response.choices[0].message.content.strip()


def main() -> None:
    load_dotenv()

    try:
        faq_context = load_faq()
        client = create_client()
    except (FileNotFoundError, RuntimeError) as error:
        print(f"\nError de configuración: {error}")
        return

    print("=" * 70)
    print(" PARACHUTE S.A. - AGENTE FAQ")
    print("=" * 70)
    print("Base de conocimiento cargada desde:")
    print(f"  {FAQ_FILE.name}")
    print("\nEscribe tu pregunta. Para salir escribe 'Bye' o presiona Ctrl-C.")
    print("-" * 70)

    while True:
        try:
            question = input("\nTú: ").strip()

            if not question:
                continue

            if question.lower() == "bye":
                print("Agente: ¡Hasta luego!")
                break

            answer = answer_question(client, faq_context, question)
            print(f"\nAgente: {answer}")

        except KeyboardInterrupt:
            print("\n\nAgente: ¡Hasta luego!")
            break
        except Exception as error:
            print(f"\nAgente: Ocurrió un error al consultar el modelo: {error}")


if __name__ == "__main__":
    main()
