"""
agents/summarizer.py — Agente Resumidor con tool use

El modelo puede cargar documentos y dividir textos largos usando tools.
Decide si necesita cargar un archivo o trabajar con el texto del mensaje.
"""

from utils.llm_client import call_llm_with_tools
from utils.logger import log_event
from tools.doc_loader import load_document
from tools.chunk_text import chunk_text
from tools.format_output import format_summary
from state import AcademicState


# ── Definición de tools ───────────────────────────────────────────────────────

SUMMARIZER_TOOLS = [
    {
        "name": "load_document",
        "description": (
            "Carga el contenido de un archivo desde la carpeta data/. "
            "Soporta .txt, .md y .pdf. Usar cuando el usuario menciona "
            "un archivo específico o pide resumir un documento."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Nombre del archivo con extensión. Ej: 'apuntes.pdf'",
                }
            },
            "required": ["filename"],
        },
    },
    {
        "name": "chunk_text",
        "description": (
            "Divide un texto largo en fragmentos más pequeños para procesarlos "
            "sin superar el límite de contexto. Retorna los fragmentos numerados. "
            "Usar cuando el texto a resumir es muy extenso (más de 3000 caracteres)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Texto largo a dividir en fragmentos",
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Tamaño máximo de cada fragmento en caracteres (default: 2500)",
                },
            },
            "required": ["text"],
        },
    },
]

# Adaptadores para las tools
SUMMARIZER_TOOL_EXECUTOR = {
    "load_document": lambda filename: load_document(f"data/{filename}") or
                     f"No se encontró el archivo '{filename}' en data/.",
    "chunk_text": lambda text, max_chars=2500: "\n\n---FRAGMENTO---\n\n".join(
        chunk_text(text, max_chars=int(max_chars))
    ),
}


# ── Agente ────────────────────────────────────────────────────────────────────

def _load_prompt() -> str:
    with open("prompts/summarizer.txt", "r", encoding="utf-8") as f:
        return f.read()


def summarizer_agent(state: AcademicState) -> AcademicState:
    """
    Nodo resumidor del grafo LangGraph.

    Lee:    state["user_input"], state["document_text"], state["topics"]
    Escribe: state["summary"]

    El modelo decide si cargar un archivo con load_document,
    si dividir el texto con chunk_text, o trabajar directamente
    con el texto disponible en el mensaje.
    """
    log_event("summarizer", "Iniciando generación de resumen con tool use")

    user_input    = state["user_input"]
    document_text = state.get("document_text") or ""
    topics        = state.get("topics") or []
    topics_str    = ", ".join(topics) if topics else "sin especificar"

    # Fix problema 7: antes se truncaba a 500 caracteres con document_text[:500],
    # lo que hacía que el modelo viera casi nada del documento pre-cargado
    # y tuviera que llamar a load_document de vuelta de forma redundante.
    # Ahora se pasa el texto completo. Si es muy largo, el modelo puede invocar
    # chunk_text por sí mismo para manejarlo en fragmentos.
    if document_text:
        doc_context = f"\nDocumento ya cargado en el sistema:\n{document_text}"
    else:
        doc_context = (
            "\nNo hay documento pre-cargado. "
            "Usa load_document si el usuario menciona un archivo específico."
        )

    prompt_template = _load_prompt()
    prompt = prompt_template.format(
        user_input=user_input,
        topics=topics_str,
        text=doc_context,
    )

    raw_summary = call_llm_with_tools(
        prompt=prompt,
        tools=SUMMARIZER_TOOLS,
        tool_executor=SUMMARIZER_TOOL_EXECUTOR,
        temperature=0.4,
    )

    # Formatear en Markdown estructurado
    formatted = format_summary(raw_summary, topics)

    log_event("summarizer", "Resumen generado exitosamente")

    return {
        **state,
        "summary": formatted,
    }