"""
agents/planner.py — Agente Planificador con tool use

El modelo puede invocar split_topics y generate_schedule
para construir el plan. Decide el orden y cuántas veces usarlas.
"""

from utils.llm_client import call_llm_with_tools
from utils.logger import log_event
from tools.topic_splitter import split_topics
from tools.study_schedule_generator import generate_schedule
from state import AcademicState


# ── Definición de tools ───────────────────────────────────────────────────────

PLANNER_TOOLS = [
    {
        "name": "split_topics",
        "description": (
            "Descompone una lista de temas generales en subtemas más concretos "
            "y manejables para estudiar. Retorna una lista de subtemas."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topics": {
                    "type": "string",
                    "description": "Temas separados por coma. Ej: 'cálculo, álgebra'",
                },
                "user_input": {
                    "type": "string",
                    "description": "Mensaje original del usuario para contexto adicional",
                },
            },
            "required": ["topics", "user_input"],
        },
    },
    {
        "name": "generate_schedule",
        "description": (
            "Distribuye una lista de subtemas en un cronograma semanal. "
            "Retorna el cronograma como texto con semanas y temas asignados."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topics": {
                    "type": "string",
                    "description": "Subtemas separados por coma a distribuir en semanas",
                },
                "topics_per_week": {
                    "type": "integer",
                    "description": "Cuántos temas estudiar por semana (default: 2)",
                },
            },
            "required": ["topics"],
        },
    },
]

# Adaptadores: las tools del modelo reciben strings, las funciones Python listas.
# Fix problema 6 (aplicado aquí también): split_topics ahora acepta separadores
# múltiples internamente, pero el adaptador sigue siendo consistente.
PLANNER_TOOL_EXECUTOR = {
    "split_topics": lambda topics, user_input="": str(
        split_topics([t.strip() for t in topics.split(",")], user_input)
    ),
    "generate_schedule": lambda topics, topics_per_week=2: generate_schedule(
        [t.strip() for t in topics.split(",")],
        topics_per_week=int(topics_per_week),
    ),
}


# ── Agente ────────────────────────────────────────────────────────────────────

def _load_prompt() -> str:
    with open("prompts/planner.txt", "r", encoding="utf-8") as f:
        return f.read()


def planner_agent(state: AcademicState) -> AcademicState:
    """
    Nodo planificador del grafo LangGraph.

    Lee:    state["user_input"], state["topics"]
    Escribe: state["plan"]

    El modelo recibe la solicitud del estudiante y las tools disponibles.
    Decide autónomamente: primero split_topics para granularidad,
    luego generate_schedule para el cronograma, finalmente redacta el plan.

    Fix problema 11: se eliminó el campo {raw_schedule} del format() porque
    el prompt nunca recibía un cronograma real — siempre era el string fijo
    "Usa las tools para generar el cronograma paso a paso." Ahora el prompt
    le indica directamente al modelo que use las tools, sin un placeholder
    que induce a pensar que recibirá datos pre-calculados.
    """
    log_event("planner", "Iniciando generación de plan con tool use")

    user_input = state["user_input"]
    topics     = state.get("topics") or []
    topics_str = ", ".join(topics) if topics else "sin especificar"

    prompt_template = _load_prompt()

    # Fix problema 11: se removió raw_schedule del .format()
    prompt = prompt_template.format(
        user_input=user_input,
        topics=topics_str,
    )

    plan = call_llm_with_tools(
        prompt=prompt,
        tools=PLANNER_TOOLS,
        tool_executor=PLANNER_TOOL_EXECUTOR,
        temperature=0.3,
    )

    log_event("planner", "Plan de estudio generado exitosamente")

    return {
        **state,
        "plan": plan,
    }