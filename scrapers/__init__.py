"""
Paquete de scrapers de PcComponentes.

Modulos principales:
    listado_ram  - Catalogo de productos (URL, nombre, ID).
    detalle_ram  - Ficha de producto (precio, opiniones, resenas, especificaciones).
    utilidades   - HTTP, JSON-LD, persistencia y deteccion de bloqueos.
"""

from scrapers.detalle_ram import ejecutar_detalle
from scrapers.listado_ram import ejecutar_listado

__all__ = ["ejecutar_listado", "ejecutar_detalle"]