"""
tools/doc_loader.py — Carga documentos desde data/

Soporta archivos .txt, .md y .pdf.
Para PDF requiere pypdf (pip install pypdf).
"""

import os

PYPDF_AVAILABLE = False
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    pass


def load_document(filepath: str) -> str:
    """
    Lee el contenido de un archivo de texto o PDF.

    Args:
        filepath: Ruta al archivo (relativa o absoluta)

    Returns:
        Contenido del archivo como string.
        Vacío si el archivo no existe o no se puede leer.
    """
    if not os.path.exists(filepath):
        return ""

    ext = os.path.splitext(filepath)[1].lower()

    if ext in [".txt", ".md"]:
        return _load_text(filepath)
    elif ext == ".pdf":
        return _load_pdf(filepath)

    return ""


def _load_text(filepath: str) -> str:
    """Lee un archivo de texto plano."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _load_pdf(filepath: str) -> str:
    """Extrae el texto de un PDF página por página."""
    if not PYPDF_AVAILABLE:
        return ""
    try:
        reader = PdfReader(filepath)
        pages  = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)
    except Exception:
        return ""