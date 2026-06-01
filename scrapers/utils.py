"""Funciones comunes para los scrapers."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def get_raw_data_path(category: str, filename: str) -> Path:
    """Construye una ruta dentro de data/raw para una categoria concreta."""
    return RAW_DATA_DIR / category / filename
