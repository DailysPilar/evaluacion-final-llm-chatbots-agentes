"""
tools/study_schedule_generator.py — Genera un cronograma de estudio

Distribuye subtemas en semanas de forma equitativa.
Lógica pura en Python, sin llamadas a LLM.
"""

import math


def generate_schedule(topics: list[str], topics_per_week: int = 2) -> str:
    """
    Distribuye una lista de temas en semanas de estudio.

    Args:
        topics:           Lista de temas/subtemas a distribuir
        topics_per_week:  Cuántos temas estudiar por semana (default: 2)

    Returns:
        String con el cronograma en formato legible para el LLM.
    """
    if not topics:
        return "Sin temas especificados."

    num_weeks = math.ceil(len(topics) / topics_per_week)
    schedule_lines = []

    for week in range(1, num_weeks + 1):
        start = (week - 1) * topics_per_week
        end   = start + topics_per_week
        week_topics = topics[start:end]
        topics_str  = " | ".join(week_topics)
        schedule_lines.append(f"Semana {week}: {topics_str}")

    return "\n".join(schedule_lines)