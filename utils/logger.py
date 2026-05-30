"""
utils/logger.py — Logger simple para debug y trazabilidad

Registra eventos de cada agente con timestamp.
Los logs se muestran en consola y se guardan en logs/app.log.
"""

import logging
import os
from datetime import datetime

# Crear carpeta de logs si no existe
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),                          # consola
        logging.FileHandler("logs/app.log", encoding="utf-8"),  # archivo
    ],
)

logger = logging.getLogger("academic_assistant")


def log_event(agent: str, message: str) -> None:
    """
    Registra un evento de un agente específico.

    Args:
        agent:   Nombre del agente (router, planner, tutor, etc.)
        message: Descripción del evento
    """
    logger.info(f"[{agent.upper()}] {message}")