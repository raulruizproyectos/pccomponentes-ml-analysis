"""
Scraper de LISTADO de tarjetas gráficas (PENDIENTE).

Este módulo es el equivalente a `listado_ram.py` pero para la categoría
de GPUs. Se recomienda usar `listado_ram.py` + `utilidades.py` como
plantilla de referencia (misma estructura de Config, paralelismo por
página, extracción vía JSON-LD ItemList, deduplicación por URL, etc.).

Cuando se implemente:
    - Reutilizar al máximo las funciones de utilidades.py
      (extraer_paginacion_categoria, extraer_item_list, etc.).
    - Añadir settings nuevos en config/settings.py (GPU_CATEGORIA_URL, etc.).
    - Seguir exactamente el mismo patrón de "modo parcial vs completo".
"""
