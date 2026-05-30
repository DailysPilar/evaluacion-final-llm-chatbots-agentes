"""
agents/validator.py — Agente Validador / Formateador

Responsabilidad: recibir la salida de cualquiera de los tres agentes,
verificar que sea válida y formatearla como respuesta final lista para
mostrar en Streamlit.

También maneja el caso de intent "desconocido" y los reintentos.
"""

from utils.logger import log_event
from state import AcademicState

# Máximo de reintentos antes de devolver un mensaje de error al usuario
MAX_RETRIES = 2


def validator_agent(state: AcademicState) -> AcademicState:
    """
    Nodo validador del grafo LangGraph.

    Lee:    state["intent"], state["plan"], state["explanation"],
            state["summary"], state["retry_count"]
    Escribe: state["final_response"], state["error"], state["retry_count"]

    Lógica:
      - Si hay una respuesta válida del agente correspondiente → formatearla
      - Si la respuesta está vacía → incrementar retry_count y marcar error
      - Si intent es "desconocido" → responder con mensaje de ayuda
    """
    log_event("validator", "Validando respuesta del agente")

    intent = state.get("intent", "desconocido")
    retry_count = state.get("retry_count", 0)

    # Obtener la respuesta según el intent
    agent_response = _get_agent_response(state, intent)

    # Caso: intent no reconocido
    if intent == "desconocido":
        return {
            **state,
            "final_response": _unknown_intent_message(),
            "error": None,
        }

    # Caso: respuesta vacía o inválida
    if not _is_valid_response(agent_response):
        log_event("validator", f"Respuesta inválida. Retry {retry_count + 1}/{MAX_RETRIES}")
        return {
            **state,
            "retry_count": retry_count + 1,
            "error": f"El agente '{intent}' no generó una respuesta válida.",
            "final_response": None,
        }

    # Caso: respuesta válida → formatear y entregar
    formatted = _format_response(agent_response, intent)
    log_event("validator", "Respuesta validada y formateada correctamente")

    return {
        **state,
        "final_response": formatted,
        "error": None,
    }


def should_retry(state: AcademicState) -> str:
    """
    Función de ruteo condicional post-validador para LangGraph.

    Retorna:
      "retry"   → si hay error y no se superó el límite de reintentos
      "end"     → si la respuesta es válida o se agotaron los reintentos
    """
    error = state.get("error")
    retry_count = state.get("retry_count", 0)

    if error and retry_count <= MAX_RETRIES:
        log_event("validator", f"Reintentando... ({retry_count}/{MAX_RETRIES})")
        return "retry"

    if error and retry_count > MAX_RETRIES:
        # Agotar reintentos: poner mensaje de error como respuesta final
        log_event("validator", "Reintentos agotados. Entregando error al usuario.")
        return "end"

    return "end"


# ---- helpers privados ----

def _get_agent_response(state: AcademicState, intent: str) -> str:
    """Obtiene la respuesta del agente correspondiente al intent."""
    mapping = {
        "planificar": state.get("plan"),
        "explicar":   state.get("explanation"),
        "resumir":    state.get("summary"),
    }
    return mapping.get(intent, "")


def _is_valid_response(response: str) -> bool:
    """
    Verifica que la respuesta no esté vacía ni sea un error del modelo.
    Se puede extender para validar estructura Markdown, longitud mínima, etc.
    """
    if not response:
        return False
    if len(response.strip()) < 50:
        return False
    # Detectar si el modelo devolvió un mensaje de error genérico
    error_phrases = ["no sé", "no puedo", "error", "lo siento, no"]
    response_lower = response.lower()
    if any(phrase in response_lower for phrase in error_phrases):
        return False
    return True


def _format_response(response: str, intent: str) -> str:
    """
    Añade un encabezado contextual según el tipo de respuesta.
    El resultado se renderiza como Markdown en Streamlit.
    """
    headers = {
        "planificar": "## 📅 Tu plan de estudio",
        "explicar":   "## 💡 Explicación del concepto",
        "resumir":    "## 📄 Resumen generado",
    }
    header = headers.get(intent, "## Respuesta")
    return f"{header}\n\n{response}"


def _unknown_intent_message() -> str:
    """Mensaje de ayuda cuando el intent no fue reconocido."""
    return (
        "## ¿En qué puedo ayudarte?\n\n"
        "No entendí bien tu solicitud. Puedo ayudarte con:\n\n"
        "- 📅 **Planificar** tu estudio: *\"Quiero estudiar álgebra lineal en 3 semanas\"*\n"
        "- 💡 **Explicar** un concepto: *\"Explícame qué es una derivada\"*\n"
        "- 📄 **Resumir** un tema o documento: *\"Resume el tema de termodinámica\"*"
    )