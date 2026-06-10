"""
CLI de entrada principal para el scraping de memorias RAM.

Proporciona una interfaz cómoda y segura sobre los módulos
listado_ram.py y detalle_ram.py.

Fases disponibles:
    listado  → Solo genera el catálogo (IDs + URLs + datos básicos de listing).
    detalle  → Procesa cada ficha individual (precio real, opiniones,
               reseñas embebidas, especificaciones técnicas).
    todo     → listado + detalle en secuencia (útil para ejecuciones frescas).

Características de la fase "detalle":
    - Reanudación inteligente (--reanudar).
    - Protección contra bloqueos reales (guarda progreso y sale con código 2).
    - Los productos sin datos (sin Product/opiniones) se saltan y se registran
      en "errores"; no paran el scraper.
    - Checkpoints periódicos para no perder horas de trabajo.
    - Delay configurable entre peticiones (respeto al sitio).

Ejemplos de uso:
    # Prueba rápida (5 páginas × 10 productos)
    python ejecutar_scraper.py listado

    # Catálogo completo (todo el sitio)
    python ejecutar_scraper.py listado --completo

    # Detalle reanudando donde lo dejamos (salta productos sin datos)
    python ejecutar_scraper.py detalle --reanudar

    # Todo desde cero con logs detallados
    python ejecutar_scraper.py todo --completo --debug

    # Detalle con pausa más agresiva (más seguro)
    python ejecutar_scraper.py detalle --delay 6.0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import RAM_DETALLE_DELAY_SECONDS
from scrapers.detalle_ram import ejecutar_detalle
from scrapers.listado_ram import ejecutar_listado

# Código de salida cuando detalle_ram detecta un BLOQUEO REAL
# (Cloudflare, captcha, rate-limit...). Los "productos sin datos" se
# tratan como errores recuperables y NO provocan este código.
CODIGO_SALIDA_BLOQUEO = 2


def _crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scraping de memorias RAM en PcComponentes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ficheros generados:\n"
            "  comun/datos/brutos/ram/listado_ram.json\n"
            "  comun/datos/brutos/ram/detalle_ram.json\n"
        ),
    )

    parser.add_argument(
        "fase",
        choices=["listado", "detalle", "todo"],
        help="listado | detalle | todo (ambas fases)",
    )
    parser.add_argument("--debug", action="store_true", help="Log DEBUG en consola")

    # --- Listado ---
    parser.add_argument(
        "--productos-por-pagina",
        type=int,
        default=None,
        metavar="N",
        help="Productos por pagina en modo parcial (default: settings)",
    )
    parser.add_argument(
        "--paginas",
        type=int,
        default=None,
        metavar="N",
        help="Paginas del listado en modo parcial (default: settings)",
    )
    parser.add_argument(
        "--completo",
        action="store_true",
        help="Listado de todo el catalogo (~42 paginas, ~1672 productos)",
    )

    # --- Detalle ---
    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        metavar="SEG",
        help=f"Segundos entre fichas (default: {RAM_DETALLE_DELAY_SECONDS})",
    )
    parser.add_argument(
        "--reanudar",
        action="store_true",
        help="Reanudar detalle desde detalle_ram.json",
    )
    parser.add_argument(
        "--desde-cero",
        action="store_true",
        help="Ignorar progreso previo en detalle",
    )

    return parser


def _kwargs_listado(args: argparse.Namespace) -> dict:
    opciones = {"debug": args.debug, "modo_completo": args.completo}
    if args.productos_por_pagina is not None:
        opciones["productos_por_pagina"] = args.productos_por_pagina
    if args.paginas is not None:
        opciones["paginas"] = args.paginas
    return opciones


def _kwargs_detalle(args: argparse.Namespace) -> dict:
    return {
        "debug": args.debug,
        "reanudar": args.reanudar,
        "desde_cero": args.desde_cero,
        "delay_segundos": args.delay if args.delay is not None else RAM_DETALLE_DELAY_SECONDS,
    }


def main() -> int:
    args = _crear_parser().parse_args()

    try:
        if args.fase in ("listado", "todo"):
            ejecutar_listado(**_kwargs_listado(args))

        if args.fase in ("detalle", "todo"):
            ejecutar_detalle(**_kwargs_detalle(args))

    except SystemExit as salida:
        if salida.code == CODIGO_SALIDA_BLOQUEO:
            return CODIGO_SALIDA_BLOQUEO
        return int(salida.code) if isinstance(salida.code, int) else 1

    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())