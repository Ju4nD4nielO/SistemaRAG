Parachute S.A. - Agente FAQ con RAG simple
Demo para implementar un agente básico de preguntas frecuentes para
Parachute S.A. utilizando una arquitectura RAG simple y una API compatible
con el esquema de OpenAI.
Arquitectura
El proyecto utiliza la versión más sencilla de RAG solicitada en la hoja:
Retrieval: se carga el archivo `FAQs_Parachute_SA_Guatemala_2026.txt`
desde el sistema de archivos.
Augmentation: el contenido completo del archivo se inyecta como
contexto en la solicitud al modelo.
Generation: el modelo responde utilizando únicamente ese contexto.
No se utiliza una base vectorial porque el enunciado solicita explícitamente
una arquitectura simple para un demo.
Tecnologías
Python
OpenAI Python SDK
Groq como proveedor del modelo
`python-dotenv` para manejar la API Key
Modelo `openai/gpt-oss-20b`
Groq ofrece compatibilidad con el cliente de OpenAI cambiando el `base_url`
a `https://api.groq.com/openai/v1`.
Instalación
Se recomienda Python 3.10+.
```bash
python -m venv .venv
```
Windows
```bash
.venv\Scripts\activate
```
Linux / macOS
```bash
source .venv/bin/activate
```
Instalar dependencias:
```bash
pip install -r requirements.txt
```
Configuración de la API Key
Copia `.env.example` como `.env`:
```bash
copy .env.example .env
```
En Linux/macOS:
```bash
cp .env.example .env
```
Luego coloca tu API Key:
```env
GROQ_API_KEY=tu_api_key_aqui
```
Nunca subas `.env` al repositorio. Ya está incluido en `.gitignore`.
Ejecutar
```bash
python main.py
```
El programa permanecerá en un loop permitiendo realizar múltiples preguntas.
Para terminar:
```text
Bye
```
o presiona:
```text
Ctrl-C
```
Ejemplos para la demostración
Preguntas que sí están en las FAQs:
```text
¿Cuándo y dónde se realizará el evento?
¿Qué peso máximo puedo tener para saltar?
¿Necesito experiencia previa?
¿Qué métodos de pago aceptan?
¿Qué ropa debo llevar?
¿Cuánto dura la experiencia completa?
```
Pregunta que no está en las FAQs:
```text
¿Cuánto cuesta el boleto?
```
El agente debe reconocer que esa información no está disponible y no
inventar un precio.
Seguridad
La API Key se obtiene mediante la variable de entorno `GROQ_API_KEY`.
No se almacena en el código fuente ni en el repositorio.
Estructura
```text
parachute-rag/
├── FAQs_Parachute_SA_Guatemala_2026.txt
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```