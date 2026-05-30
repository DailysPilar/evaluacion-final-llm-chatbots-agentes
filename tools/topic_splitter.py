"""
tools/topic_splitter.py — Divide temas en subtemas concretos

Lógica pura en Python, sin llamadas a LLM.
Útil para que el planificador tenga una granularidad adecuada.
"""

# Mapa de subtemas predefinidos para materias comunes
# Se puede ampliar o reemplazar por una llamada al LLM si se prefiere
SUBTOPICS_MAP = {
    "cálculo": ["Límites y continuidad", "Derivadas", "Reglas de derivación",
                "Aplicaciones de la derivada", "Integrales", "Técnicas de integración"],
    "álgebra": ["Sistemas de ecuaciones", "Matrices", "Determinantes",
                "Vectores", "Espacios vectoriales", "Transformaciones lineales"],
    "estadística": ["Probabilidad básica", "Distribuciones", "Estadística descriptiva",
                    "Inferencia estadística", "Pruebas de hipótesis", "Regresión"],
    "física": ["Cinemática", "Dinámica", "Trabajo y energía",
               "Termodinámica", "Ondas", "Electromagnetismo"],
    "programación": ["Variables y tipos", "Estructuras de control", "Funciones",
                     "Listas y diccionarios", "POO", "Manejo de errores"],
}


def split_topics(topics: list[str], user_input: str) -> list[str]:
    """
    Descompone una lista de temas en subtemas más granulares.

    Args:
        topics:     Lista de temas extraídos por el router
        user_input: Mensaje original del usuario (para búsqueda adicional)

    Returns:
        Lista de subtemas. Si no hay coincidencias, devuelve los temas originales.
    """
    subtopics = []

    all_text = " ".join(topics + [user_input]).lower()

    for keyword, subs in SUBTOPICS_MAP.items():
        if keyword in all_text:
            subtopics.extend(subs)

    # Si no hubo coincidencias, devolver los temas originales
    return subtopics if subtopics else topics