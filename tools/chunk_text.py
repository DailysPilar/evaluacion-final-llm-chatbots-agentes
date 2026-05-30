"""
tools/chunk_text.py — Divide texto largo en fragmentos

Evita que el contexto de Ollama se sature con textos muy largos.
"""


def chunk_text(text: str, max_chars: int = 2500) -> list[str]:
    """
    Divide un texto largo en fragmentos respetando párrafos.

    Args:
        text:      Texto a dividir
        max_chars: Tamaño máximo de cada chunk en caracteres

    Returns:
        Lista de strings, cada uno de máximo max_chars caracteres.
    """
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        # Si el párrafo solo ya es más grande que el límite, cortarlo por fuerza
        if len(paragraph) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            # Cortar el párrafo largo en trozos simples
            for i in range(0, len(paragraph), max_chars):
                chunks.append(paragraph[i:i + max_chars])
            continue

        # Si añadir el párrafo supera el límite, guardar chunk actual y empezar uno nuevo
        if len(current_chunk) + len(paragraph) + 2 > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            current_chunk += "\n\n" + paragraph if current_chunk else paragraph

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks