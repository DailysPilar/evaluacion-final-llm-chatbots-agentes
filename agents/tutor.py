"""
agents/tutor.py — Agente Tutor con tool use

El modelo decide autónomamente si buscar en documentos locales (RAG)
o en Wikipedia según la pregunta. No hay lógica de decisión en Python:
es el LLM quien elige qué tool invocar y cuándo.
"""

from utils.llm_client import call_llm_with_tools
from utils.logger import log_event
from tools.retriever import retrieve_context
from tools.wikipedia_search import search_wikipedia
from state import AcademicState


# ── Definición de tools (formato unificado Ollama/Gemini) ─────────────────────

TUTOR_TOOLS = [
    {
        "name": "retrieve_context",
        "description": (
            "Busca información relevante en los documentos académicos del usuario "
            "(apuntes, libros, PDFs subidos). Usar cuando la pregunta puede estar "
            "cubierta por material propio del estudiante."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Término o frase a buscar en los documentos",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_wikipedia",
        "description": (
            "Busca una definición o explicación en Wikipedia en español. "
            "Usar cuando no hay documentos propios disponibles o como complemento."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Concepto o término a buscar en Wikipedia",
                }
            },
            "required": ["query"],
        },
    },
]

# Mapa nombre_tool → función Python real
TUTOR_TOOL_EXECUTOR = {
    "retrieve_context": lambda query: retrieve_context(query),
    "search_wikipedia": lambda query: search_wikipedia(query),
}


# ── Agente ────────────────────────────────────────────────────────────────────

def _load_prompt() -> str:
    with open("prompts/tutor.txt", "r", encoding="utf-8") as f:
        return f.read()


def tutor_agent(state: AcademicState) -> AcademicState:
    """
    Nodo tutor del grafo LangGraph.

    Lee:    state["user_input"], state["topics"]
    Escribe: state["explanation"]

    El modelo recibe la pregunta + las definiciones de tools y decide
    autónomamente si buscar en documentos locales, en Wikipedia, en ambos,
    o en ninguno. El loop de tool use se maneja en llm_client.py.
    """
    log_event("tutor", "Iniciando explicación de concepto con tool use")

    user_input = state["user_input"]
    topics     = state.get("topics") or []
    topics_str = ", ".join(topics) if topics else "sin especificar"

    prompt_template = _load_prompt()
    prompt = prompt_template.format(
        user_input=user_input,
        topics=topics_str,
        # El contexto ya no se inyecta aquí: el modelo lo busca con las tools
        context="Usa las tools disponibles para buscar contexto relevante.",
    )

    explanation = call_llm_with_tools(
        prompt=prompt,
        tools=TUTOR_TOOLS,
        tool_executor=TUTOR_TOOL_EXECUTOR,
        temperature=0.5,
    )

    log_event("tutor", "Explicación generada exitosamente")

    return {
        **state,
        "explanation": explanation,
    }