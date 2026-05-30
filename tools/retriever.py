"""
tools/retriever.py — RAG sobre documentos locales en data/

Usa ChromaDB + embeddings para buscar fragmentos relevantes
según una query de texto.
"""

import os

CHROMA_AVAILABLE = False
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    pass


def retrieve_context(query: str, top_k: int = 3) -> str:
    """
    Busca los fragmentos más relevantes en la base vectorial local.

    Args:
        query:  Texto de búsqueda
        top_k:  Número de fragmentos a recuperar

    Returns:
        Contexto concatenado como string. Vacío si no hay documentos indexados.
    """
    if not CHROMA_AVAILABLE:
        return ""

    db_path = "data/chroma_db"
    if not os.path.exists(db_path):
        return ""

    try:
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_or_create_collection("academic_docs")

        if collection.count() == 0:
            return ""

        results = collection.query(query_texts=[query], n_results=top_k)
        documents = results.get("documents", [[]])[0]
        return "\n\n".join(documents)

    except Exception:
        return ""
