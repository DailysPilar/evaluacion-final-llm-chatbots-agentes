"""
workflow.py — Definición del grafo LangGraph

Construye y compila el grafo principal del asistente académico.
Importa todos los agentes y conecta los nodos con edges normales
y edges condicionales para el ruteo y los reintentos.

Uso desde app.py:
    from workflow import build_graph
    graph = build_graph()
    result = graph.invoke(initial_state)
"""

from langgraph.graph import StateGraph, END

from state import AcademicState
from agents.router import router_agent, route_to_agent
from agents.planner import planner_agent
from agents.tutor import tutor_agent
from agents.summarizer import summarizer_agent
from agents.validator import validator_agent, should_retry


def build_graph() -> StateGraph:
    """
    Construye y compila el grafo LangGraph del asistente académico.

    Estructura del grafo:
        START
          ↓
        router  ──(condicional)──→  planner ──→ validator
                                →  tutor    ──→ validator
                                →  summarizer → validator
                                → (desconocido) → validator
          ↑                             ↓
          └────────(retry)──────────────┘
                                        ↓ (end)
                                       END

    Returns:
        Grafo compilado listo para invocar con .invoke(state)
    """

    # --- 1. Crear el grafo con el estado tipado ---
    graph = StateGraph(AcademicState)

    # --- 2. Registrar los nodos ---
    # Cada nodo recibe el estado completo y devuelve un estado actualizado
    graph.add_node("router",     router_agent)
    graph.add_node("planner",    planner_agent)
    graph.add_node("tutor",      tutor_agent)
    graph.add_node("summarizer", summarizer_agent)
    graph.add_node("validator",  validator_agent)

    # --- 3. Definir el punto de entrada ---
    graph.set_entry_point("router")

    # --- 4. Edge condicional: router → agente según intent ---
    # route_to_agent() devuelve "planner", "tutor", "summarizer" o "validator"
    graph.add_conditional_edges(
        source="router",
        path=route_to_agent,
        path_map={
            "planner":    "planner",
            "tutor":      "tutor",
            "summarizer": "summarizer",
            "validator":  "validator",   # intent desconocido va directo a validator
        },
    )

    # --- 5. Edges directos: cada agente → validador ---
    graph.add_edge("planner",    "validator")
    graph.add_edge("tutor",      "validator")
    graph.add_edge("summarizer", "validator")

    # --- 6. Edge condicional: validador → retry o END ---
    # should_retry() devuelve "retry" o "end"
    graph.add_conditional_edges(
        source="validator",
        path=should_retry,
        path_map={
            "retry": "router",   # reenviar al router para reintentar
            "end":   END,        # entregar respuesta final a Streamlit
        },
    )

    # --- 7. Compilar y retornar ---
    compiled = graph.compile()
    return compiled


# ---- Ejecución directa para testing rápido ----
if __name__ == "__main__":
    from state import create_initial_state

    graph = build_graph()

    # Test 1: planificar
    state = create_initial_state("Quiero estudiar cálculo diferencial en dos semanas")
    result = graph.invoke(state)
    print("=== PLANIFICADOR ===")
    print(result["final_response"])

    # Test 2: explicar
    state = create_initial_state("Explícame qué es una transformada de Fourier")
    result = graph.invoke(state)
    print("\n=== TUTOR ===")
    print(result["final_response"])

    # Test 3: resumir
    state = create_initial_state("Resume el tema de fotosíntesis")
    result = graph.invoke(state)
    print("\n=== RESUMIDOR ===")
    print(result["final_response"])