"""
Configuración central del proyecto pccomponentes-ml-analysis.

Aquí se definen:
  - Rutas absolutas de los ficheros JSON de trabajo (nunca hardcodearlas).
  - Parámetros de comportamiento de los scrapers de RAM (para que sean
    fáciles de ajustar sin tocar código).
  - Constantes compartidas (delays, timeouts, tamaños mínimos de HTML, etc.).

Recomendación:
    Para un run "amable" con el sitio: RAM_DETALLE_DELAY_SECONDS >= 3-4s.
    Para desarrollo rápido: usa el modo parcial del CLI (pocas páginas).
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Rutas de datos brutos (estandarizado en data/brutos/)
DATA_DIR = PROJECT_ROOT / "data"
BRUTOS_DATA_DIR = DATA_DIR / "brutos"

# ---------------------------------------------------------------------------
# Scraper de memorias RAM (PcComponentes)
# ---------------------------------------------------------------------------

RAM_DATA_DIR = BRUTOS_DATA_DIR / "ram"
RAM_LISTADO_JSON = RAM_DATA_DIR / "listado_ram.json"
RAM_DETALLE_JSON = RAM_DATA_DIR / "detalle_ram.json"

RAM_CATEGORIA_URL = "https://www.pccomponentes.com/memorias-ram"

# -----------------------------------------------------------------------------
# Listado (categoría)
# -----------------------------------------------------------------------------
# Modo parcial por defecto (rápido para desarrollo y pruebas)
RAM_PAGINAS_LISTADO = 5
RAM_PRODUCTOS_POR_PAGINA = 10
RAM_MAX_WORKERS_LISTADO = 5

# Modo completo (--completo). El sitio tiene ~42 páginas y ~1670 productos.
RAM_MAX_WORKERS_LISTADO_COMPLETO = 8

# -----------------------------------------------------------------------------
# Detalle (ficha de producto)
# -----------------------------------------------------------------------------
# Pausa entre descargas de fichas. 4s es un valor prudente.
# Subirlo a 5-6s si empiezas a recibir bloqueos frecuentes.
RAM_DETALLE_DELAY_SECONDS = 4.0

# Cada cuántos productos procesados guardamos el JSON completo como checkpoint.
# Con 1646 productos y 25 → ~65 checkpoints durante un run completo.
RAM_DETALLE_CHECKPOINT_CADA = 25

# Tamaño mínimo razonable de una ficha de producto en bytes.
# Si el HTML es más pequeño casi seguro es una página de error/bloqueo.
RAM_HTML_MINIMO_FICHA_BYTES = 50_000

# HTTP generico (otros modulos del proyecto)
REQUEST_DELAY_SECONDS = 2.0
REQUEST_TIMEOUT_SECONDS = 30