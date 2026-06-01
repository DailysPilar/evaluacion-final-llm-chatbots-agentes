"""
agents/validator.py — Agente Validador

Responsabilidad:
  - Verificar que el agente anterior haya producido una respuesta no vacía
  - Armar el campo final_response con el resultado correspondiente al intent
  - Controlar el loop de reintentos usando MAX_RETRIES desde .env
  - Registrar errores claros si se agota el límite de reintentos

El validador NO llama al LLM: es lógica pura en Python.
"""

import os
from dotenv import load_dotenv
from utils.logger import log_event
from state import AcademicState

load_dotenv()

# Límite de reintentos leído desde .env (antes ignorado porque el archivo estaba vacío)
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))


def validator_agent(state: AcademicState) -> AcademicState:
    """
    Nodo validador del grafo LangGraph.

    Lee:    state["intent"], state["plan"] | state["explanation"] | state["summary"]
    Escribe: state["final_response"], state["error"], state["retry_count"]

    Lógica:
      1. Detecta qué campo de respuesta corresponde al intent activo
      2. Si el campo tiene contenido válido → arma final_response
      3. Si está vacío o es None → incrementa retry_count y registra error
    """
    intent      = state.get("intent", "desconocido")
    retry_count = state.get("retry_count", 0)

    log_event("validator", f"Validando respuesta para intent='{intent}' | retry={retry_count}")

    # Mapa intent → campo del estado donde el agente dejó su respuesta
    intent_to_field = {
        "planificar": "plan",
        "explicar":   "explanation",
        "resumir":    "summary",
    }

    response_field = intent_to_field.get(intent)
    response_value = state.get(response_field) if response_field else None

    # ── Respuesta válida ──────────────────────────────────────────────────────
    if response_value and response_value.strip():
        log_event("validator", "Respuesta válida. Preparando final_response.")
        return {
            **state,
            "final_response": response_value.strip(),
            "error": None,
        }

    # ── Respuesta inválida: decidir si reintentar ─────────────────────────────
    new_retry_count = retry_count + 1

    if new_retry_count >= MAX_RETRIES:
        # Se agotaron los reintentos: entregar mensaje de error al usuario
        error_msg = (
            f"No se pudo generar una respuesta válida para tu solicitud "
            f"después de {MAX_RETRIES} intentos.\n\n"
            f"Intent detectado: **{intent}**\n\n"
            "Por favor reformulá tu pregunta e intentá de nuevo."
        )
        log_event("validator", f"MAX_RETRIES={MAX_RETRIES} alcanzado. Finalizando con error.")
        return {
            **state,
            "final_response": error_msg,
            "error": f"Respuesta vacía tras {MAX_RETRIES} reintentos",
            "retry_count": new_retry_count,
        }

    # Todavía hay reintentos disponibles: señalar para volver al router
    log_event("validator", f"Respuesta vacía. Reintentando ({new_retry_count}/{MAX_RETRIES}).")
    return {
        **state,
        "error": f"Respuesta vacía en campo '{response_field}' (intento {new_retry_count})",
        "retry_count": new_retry_count,
        # Limpiar el campo fallido para que el agente lo regenere desde cero
        response_field: None,
    }


def should_retry(state: AcademicState) -> str:
    """
    Función de ruteo condicional para LangGraph.
    Decide si el grafo debe reintentar o finalizar.

    Returns:
        "retry" → volver al router para regenerar la respuesta
        "end"   → entregar final_response a Streamlit
    """
    retry_count = state.get("retry_count", 0)
    error       = state.get("error")
    final       = state.get("final_response")

    # Si hay respuesta final (válida o mensaje de error por agotamiento) → terminar
    if final:
        return "end"

    # Si hay error y no se agotaron los reintentos → reintentar
    if error and retry_count < MAX_RETRIES:
        return "retry"

    return "end"