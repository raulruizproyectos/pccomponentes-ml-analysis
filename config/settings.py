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

# ---------------------------------------------------------------------------
# AWS (Fase 01: S3 + Lambda + RDS)
# ---------------------------------------------------------------------------
# Las credenciales y el nombre del bucket se leen de variables de entorno.
# Ver .env.example para la plantilla.

import os

from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Prefijos S3 que replican la estructura local data/brutos y data/procesados
AWS_S3_PREFIX_BRUTOS = "brutos"
AWS_S3_PREFIX_PROCESADOS = "procesados"

PROCESADOS_DATA_DIR = DATA_DIR / "procesados"
RAM_PROCESADOS_DIR = PROCESADOS_DATA_DIR / "ram"

RAM_PROCESADOS_ARCHIVOS = {
    "productos": RAM_PROCESADOS_DIR / "productos_ram_limpios.json",
    "especificaciones": RAM_PROCESADOS_DIR / "especificaciones_ram_limpias.json",
    "distribuciones": RAM_PROCESADOS_DIR / "distribucion_valoraciones_ram_limpia.json",
    "resenas": RAM_PROCESADOS_DIR / "resenas_ram_limpias.json",
}

RAM_BRUTOS_ARCHIVOS = {
    "listado": RAM_LISTADO_JSON,
    "detalle": RAM_DETALLE_JSON,
}

# ---------------------------------------------------------------------------
# Tarjetas gráficas (rutas previstas; scraper pendiente)
# ---------------------------------------------------------------------------

GPU_DATA_DIR = BRUTOS_DATA_DIR / "tarjetas_graficas"
GPU_LISTADO_JSON = GPU_DATA_DIR / "listado_tarjetas_graficas.json"
GPU_DETALLE_JSON = GPU_DATA_DIR / "detalle_tarjetas_graficas.json"
GPU_CATEGORIA_URL = "https://www.pccomponentes.com/tarjetas-graficas"

GPU_PROCESADOS_DIR = PROCESADOS_DATA_DIR / "tarjetas_graficas"

GPU_PROCESADOS_ARCHIVOS = {
    "productos": GPU_PROCESADOS_DIR / "productos_tarjetas_graficas_limpios.json",
    "especificaciones": GPU_PROCESADOS_DIR / "especificaciones_tarjetas_graficas_limpias.json",
    "distribuciones": GPU_PROCESADOS_DIR / "distribucion_valoraciones_tarjetas_graficas_limpia.json",
    "resenas": GPU_PROCESADOS_DIR / "resenas_tarjetas_graficas_limpias.json",
}

GPU_BRUTOS_ARCHIVOS = {
    "listado": GPU_LISTADO_JSON,
    "detalle": GPU_DETALLE_JSON,
}

# Registro unificado de categorías para pipeline local y AWS
PIPELINE_CATEGORIAS = {
    "ram": {
        "slug": "ram",
        "categoria_db": "memoria_ram",
        "modulo_limpieza": "pipeline.limpieza_ram",
        "brutos": RAM_BRUTOS_ARCHIVOS,
        "procesados": RAM_PROCESADOS_ARCHIVOS,
        "lista": True,
    },
    "tarjetas_graficas": {
        "slug": "tarjetas_graficas",
        "categoria_db": "tarjeta_grafica",
        "modulo_limpieza": "pipeline.limpieza_gpu",
        "brutos": GPU_BRUTOS_ARCHIVOS,
        "procesados": GPU_PROCESADOS_ARCHIVOS,
        "lista": False,
    },
}