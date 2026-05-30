"""
tools/format_output.py — Formatea el resumen en Markdown estructurado

Asegura que todos los resúmenes tengan la misma estructura visual
independientemente de cómo haya respondido el modelo.
"""


def format_summary(raw_summary: str, topics: list[str]) -> str:
    """
    Envuelve el resumen crudo en una estructura Markdown consistente.

    Args:
        raw_summary: Texto de resumen generado por el LLM
        topics:      Lista de temas para el encabezado

    Returns:
        String Markdown con estructura: tema > contenido > nota final
    """
    topics_str = ", ".join(topics) if topics else "Tema general"

    formatted = (
        f"**Temas cubiertos:** {topics_str}\n\n"
        f"---\n\n"
        f"{raw_summary.strip()}\n\n"
        f"---\n"
        f"*Resumen generado por el Asistente Académico*"
    )

    return formatted