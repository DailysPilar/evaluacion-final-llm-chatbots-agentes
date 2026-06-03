"""
agents/router.py — Agente Router

Responsabilidad: clasificar la intención del usuario en una de tres categorías:
  - "planificar"  → el usuario quiere un plan de estudio
  - "explicar"    → el usuario quiere entender un concepto
  - "resumir"     → el usuario quiere un resumen de un tema o documento

También extrae los temas principales del mensaje para pasarlos a los agentes siguientes.
"""

import re
from utils.llm_client import call_llm
from utils.logger import log_event
from state import AcademicState


# Prompt del router cargado desde archivo separado
def _load_prompt() -> str:
    with open("prompts/router.txt", "r", encoding="utf-8") as f:
        return f.read()


def router_agent(state: AcademicState) -> AcademicState:
    """
    Nodo router del grafo LangGraph.

    Lee:    state["user_input"]
    Escribe: state["intent"], state["topics"]

    El modelo responde en formato estructurado:
        INTENT: <planificar|explicar|resumir>
        TOPICS: <tema1>, <tema2>, ...

    Si el formato falla, se usa "desconocido" como intent.
    """
    prompt_template = _load_prompt()
    prompt = prompt_template.format(user_input=state["user_input"])

    log_event("router", "Clasificando intención del usuario")

    response = call_llm(prompt)

    # Parsear la respuesta estructurada del modelo
    intent = _parse_intent(response)
    topics = _parse_topics(response)

    log_event("router", f"Intent detectado: {intent} | Topics: {topics}")
    print(f"Intent: {intent}\n, Topics: {topics}" )  # Debug adicional para verificar parsing
    return {
        "intent": intent,
        "topics": topics,
    }


def route_to_agent(state: AcademicState) -> str:
    """
    Función de ruteo condicional para LangGraph.
    Devuelve el nombre del siguiente nodo según el intent clasificado.

    Esta función se usa en workflow.py como:
        graph.add_conditional_edges("router", route_to_agent, {...})
    """
    intent = state.get("intent", "desconocido")

    routing_map = {
        "planificar": "planner",
        "explicar":   "tutor",
        "resumir":    "summarizer",
        "desconocido": "validator",   # el validador manejará el error
    }

    return routing_map.get(intent, "validator")


# ---- helpers privados ----

def _parse_intent(response: str) -> str:
    """Extrae el campo INTENT de la respuesta del modelo."""
    match = re.search(r"INTENT:\s*(planificar|explicar|resumir)", response, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return "desconocido"


def _parse_topics(response: str) -> list[str]:
    """Extrae el campo TOPICS y devuelve una lista de strings."""
    match = re.search(r"TOPICS:\s*(.+)", response, re.IGNORECASE)
    if match:
        raw = match.group(1)
        return [t.strip() for t in raw.split(",") if t.strip()]
    return []