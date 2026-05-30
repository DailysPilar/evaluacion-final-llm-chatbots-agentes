"""
tools/wikipedia_search.py — Búsqueda en Wikipedia

Recupera el resumen de un artículo de Wikipedia en español.
Se usa como fallback cuando el retriever local no tiene suficiente contexto.
"""

WIKIPEDIA_AVAILABLE = False
try:
    import wikipedia
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    pass


def search_wikipedia(query: str, sentences: int = 5) -> str:
    """
    Busca en Wikipedia y devuelve un resumen del artículo más relevante.

    Args:
        query:     Término o frase a buscar
        sentences: Número de oraciones del resumen a retornar

    Returns:
        Resumen del artículo como string. Vacío si no se encuentra nada.
    """
    if not WIKIPEDIA_AVAILABLE:
        return ""

    try:
        wikipedia.set_lang("es")
        summary = wikipedia.summary(query, sentences=sentences, auto_suggest=True)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        # Si hay ambigüedad, intentar con la primera opción
        try:
            summary = wikipedia.summary(e.options[0], sentences=sentences)
            return summary
        except Exception:
            return ""
    except wikipedia.exceptions.PageError:
        return ""
    except Exception:
        return ""