# Nexus — Asistente Académico con LangGraph

> Evaluación final · Postgrado LLMs, Chatbots y Agentes

Nexus es una aplicación de asistencia académica basada en **múltiples agentes LLM orquestados con LangGraph** e interfaz conversacional en **Streamlit**. El sistema clasifica la intención del usuario y deriva la consulta al agente especializado correspondiente: planificador, tutor o resumidor.

---

## Caso de uso elegido

**Asistente Académico** — el sistema permite:

- 📅 **Planificar** un cronograma de estudio semanal para cualquier materia
- 💡 **Explicar** conceptos con analogías, ejemplos paso a paso y resumen final
- 📝 **Resumir** temas o documentos (PDF / TXT) subidos por el usuario

---

## Arquitectura

```
Usuario (Streamlit)
        │
        ▼
   [ Router ]  ←── reintento si respuesta vacía
        │
        ├──► [ Planner ]    → plan de estudio Markdown
        ├──► [ Tutor ]      → explicación con ejemplos
        └──► [ Summarizer ] → resumen estructurado
                │
                ▼
          [ Validator ]  ──► final_response → Streamlit
```

### Agentes

| Agente | Archivo | Responsabilidad |
|---|---|---|
| **Router** | `agents/router.py` | Clasifica intent (`planificar` / `explicar` / `resumir`) y extrae topics |
| **Planner** | `agents/planner.py` | Genera plan semanal usando tools `split_topics` + `generate_schedule` |
| **Tutor** | `agents/tutor.py` | Explica conceptos, usa RAG local y Wikipedia como tools |
| **Summarizer** | `agents/summarizer.py` | Resume textos o documentos, usa `load_document` + `chunk_text` |
| **Validator** | `agents/validator.py` | Valida respuesta, controla loop de reintentos (máx. `MAX_RETRIES`) |

### Flujo LangGraph (`workflow.py`)

```
START → router → (condicional) → planner / tutor / summarizer
                                         ↓
                                     validator → (end | retry → router)
```

### Tools por agente

- **Planner**: `split_topics` (descompone materia en subtemas), `generate_schedule` (distribuye en semanas)
- **Tutor**: `retrieve_context` (RAG sobre ChromaDB local), `search_wikipedia` (fallback a Wikipedia ES)
- **Summarizer**: `load_document` (carga PDF/TXT de `data/`), `chunk_text` (divide textos largos)

---

## Decisiones de diseño

- **Provider unificado** (`utils/llm_client.py`): detecta automáticamente si hay `GEMINI_API_KEY` y usa Gemini; si no, cae a Ollama. Mismo contrato para todos los agentes.
- **Tool use nativo**: planner y tutor delegan decisiones de búsqueda/cálculo al propio LLM, sin lógica de enrutamiento en Python.
- **Validator sin LLM**: lógica pura de control; evita latencia innecesaria en el loop de validación.
- **Prompts externos**: todos en `prompts/*.txt`, separados del código para facilitar iteración.
- **RAG opcional**: ChromaDB se activa solo si `data/chroma_db/` existe; el sistema degrada elegantemente sin él.

---

## Estructura del repositorio

```
.
├── app.py                        # Interfaz Streamlit (Nexus UI)
├── workflow.py                   # Grafo LangGraph principal
├── state.py                      # AcademicState (TypedDict compartido)
├── .env.example                  # Variables de entorno (copiar a .env)
│
├── agents/
│   ├── router.py                 # Clasifica intención
│   ├── planner.py                # Genera plan de estudio
│   ├── tutor.py                  # Explica conceptos
│   ├── summarizer.py             # Resume textos/documentos
│   └── validator.py              # Valida respuestas y controla reintentos
│
├── prompts/
│   ├── router.txt
│   ├── planner.txt
│   ├── tutor.txt
│   └── summarizer.txt
│
├── tools/
│   ├── retriever.py              # RAG con ChromaDB
│   ├── wikipedia_search.py       # Búsqueda en Wikipedia ES
│   ├── doc_loader.py             # Carga PDF/TXT
│   ├── chunk_text.py             # Divide textos largos
│   ├── topic_splitter.py         # Descompone temas en subtemas
│   ├── study_schedule_generator.py  # Genera cronograma semanal
│   └── format_output.py          # Formatea resúmenes en Markdown
│
├── utils/
│   ├── llm_client.py             # Cliente LLM unificado (Gemini / Ollama)
│   └── logger.py                 # Logger a consola + logs/app.log
│
└── data/
    ├── data.txt                  # Base de conocimiento académico
    └── examples.json             # Ejemplos de uso por intent
```

---

## Instalación y uso

### Requisitos previos

- Python 3.10+
- [Ollama](https://ollama.com) instalado y corriendo **ó** una API key de Google Gemini

### 1. Clonar el repositorio

```bash
git clone https://github.com/<tu-usuario>/evaluacion-final-llm-chatbots-agentes.git
cd evaluacion-final-llm-chatbots-agentes
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

> Si no tenés `requirements.txt`, instalá manualmente:
> ```bash
> pip install streamlit langgraph langchain langchain-core python-dotenv \
>             mistune pypdf chromadb wikipedia
> # Para Gemini:
> pip install langchain-google-genai
> ```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Editá `.env` con tus valores:

```env
# Opción A: usar Google Gemini (recomendado)
GEMINI_API_KEY=tu_clave_aqui
GEMINI_MODEL=gemini-2.0-flash

# Opción B: usar Ollama local (sin clave)
# GEMINI_API_KEY=          ← dejar vacío o comentado
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama3.2:3b

# Parámetros generales
TEMPERATURE=0.7
MAX_TOKENS=2048
MAX_RETRIES=3
FILE_ENCODING=utf-8
```

### 4. (Solo Ollama) Bajar el modelo

```bash
ollama pull llama3.2:3b
ollama serve          # si no está corriendo ya
```

### 5. Ejecutar la aplicación

```bash
streamlit run app.py
```

Abrí el navegador en `http://localhost:8501`.

---

## Uso de la interfaz

| Qué querés hacer | Ejemplo de mensaje |
|---|---|
| Planificar estudio | `"Quiero estudiar álgebra lineal en 2 semanas"` |
| Explicar un concepto | `"Explicame qué es una integral definida"` |
| Resumir un tema | `"Resumí el tema de distribuciones de probabilidad"` |
| Resumir un documento | Adjuntá un PDF/TXT con el clip 📎 y pedí `"Resumí este documento"` |

- **Ctrl+Enter** para enviar mensaje
- El clip 📎 en el compositor permite subir archivos `.pdf`, `.txt` o `.md`
- El historial de conversación se muestra en el sidebar con el intent detectado por color

---

## Variables de entorno — referencia completa

| Variable | Default | Descripción |
|---|---|---|
| `GEMINI_API_KEY` | — | API key de Google AI Studio. Si está definida, activa Gemini |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Modelo Gemini a usar |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL base de Ollama |
| `DEFAULT_MODEL` | `llama3.2:3b` | Modelo Ollama (fallback si no hay Gemini) |
| `TEMPERATURE` | `0.7` | Temperatura de generación |
| `MAX_TOKENS` | `2048` | Máximo de tokens por respuesta |
| `MAX_RETRIES` | `3` | Reintentos del validator antes de entregar error |
| `FILE_ENCODING` | `utf-8` | Encoding para lectura de archivos |

---

## Dependencias principales

| Paquete | Uso |
|---|---|
| `streamlit` | Interfaz web |
| `langgraph` | Orquestación del grafo de agentes |
| `langchain`, `langchain-core` | Abstracciones LLM y mensajes |
| `langchain-google-genai` | Integración con Gemini |
| `python-dotenv` | Carga de variables de entorno |
| `mistune` | Renderizado de Markdown en el chat |
| `pypdf` | Extracción de texto de PDFs |
| `chromadb` | Base vectorial para RAG (opcional) |
| `wikipedia` | Búsqueda en Wikipedia ES (opcional) |