"""
state.py — Estado compartido del grafo LangGraph

Este TypedDict fluye a través de todos los nodos del grafo.
Cada agente puede leer y escribir campos específicos.
"""

from typing import TypedDict, Literal, Optional


# Tipos de intención reconocidos por el router
IntentType = Literal["planificar", "explicar", "resumir", "desconocido"]

# Nivel de dificultad estimado por el planificador
DifficultyLevel = Literal["fácil", "medio", "difícil"]


class AcademicState(TypedDict):
    """
    Estado compartido entre todos los agentes del asistente académico.

    Campos de entrada (escritos al inicio por app.py):
        user_input      : mensaje crudo del usuario
        document_text   : texto de un documento cargado (opcional)

    Campos de ruteo (escritos por el router):
        intent          : intención clasificada del usuario
        topics          : lista de temas extraídos del mensaje

    Campos de respuesta por agente:
        plan            : plan de estudio estructurado (Planificador)
        explanation     : explicación de concepto con ejemplos (Tutor)
        summary         : resumen estructurado (Resumidor)

    Campos de control (escritos por el validador):
        final_response  : respuesta final lista para mostrar en Streamlit
        retry_count     : número de reintentos realizados (max 2)
        error           : mensaje de error si algo falla
    """

    # --- Entrada ---
    user_input: str
    document_text: Optional[str]

    # --- Ruteo ---
    intent: Optional[IntentType]
    topics: Optional[list[str]]

    # --- Respuestas de agentes ---
    plan: Optional[str]
    explanation: Optional[str]
    summary: Optional[str]

    # --- Control ---
    final_response: Optional[str]
    retry_count: int
    error: Optional[str]


def create_initial_state(user_input: str, document_text: str = None) -> AcademicState:
    """
    Crea un estado inicial limpio para una nueva conversación.

    Args:
        user_input:     Mensaje del usuario desde Streamlit
        document_text:  Texto del documento cargado (si hay uno)

    Returns:
        AcademicState con todos los campos opcionales en None
    """
    return AcademicState(
        user_input=user_input,
        document_text=document_text,
        intent=None,
        topics=None,
        plan=None,
        explanation=None,
        summary=None,
        final_response=None,
        retry_count=0,
        error=None,
    )