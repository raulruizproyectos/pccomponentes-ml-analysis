"""
Scraper de LISTADO (categoría) de memorias RAM en PcComponentes.

Responsabilidad:
    Generar el "catálogo maestro" (listado_ram.json) que luego consume
    el scraper de detalle. Contiene solo los datos visibles en la
    página de categoría: nombre, url, precio de listado, valoración
    superficial, sku y posición.

Flujo principal:
    1. Determinar número de páginas (modo completo autodetecta vía
       extraer_paginacion_categoria o usa valores de settings).
    2. Descargar todas las páginas en paralelo (ThreadPoolExecutor).
       Cada página usa su propia Session para evitar contaminación.
    3. Extraer productos de cada página usando JSON-LD ItemList
       (la fuente más estable y limpia).
    4. Deduplicar por URL (un producto puede aparecer en varias páginas
       durante promociones o reordenamientos).
    5. Asignar IDs estables tipo "ram_0001" (con padding según el total)
       y persistir junto con metadata rica (páginas exploradas,
       errores por página, fecha, modo, etc.).

Modos de ejecución:
    - Parcial (por defecto): pocas páginas y pocos productos por página.
      Ideal para desarrollo y pruebas rápidas.
    - Completo (--completo): todo el catálogo (~42 páginas, ~1670 productos).
      Usa más workers y autodetecta la paginación real del sitio.

El resultado de este módulo es la entrada obligatoria para detalle_ram.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

from config.settings import (
    RAM_CATEGORIA_URL,
    RAM_LISTADO_JSON,
    RAM_MAX_WORKERS_LISTADO,
    RAM_MAX_WORKERS_LISTADO_COMPLETO,
    RAM_PAGINAS_LISTADO,
    RAM_PRODUCTOS_POR_PAGINA,
)
from scrapers.utilidades import (
    configurar_logger,
    crear_sesion,
    extraer_item_list,
    extraer_paginacion_categoria,
    formatear_id_ram,
    guardar_json,
    obtener_html,
    ordenar_por_posicion_listado,
    parsear_scripts_json_ld,
    timestamp_utc,
)


# -----------------------------------------------------------------------------
# Configuracion de ejecucion
# -----------------------------------------------------------------------------


@dataclass
class ConfigListado:
    """Parametros efectivos tras resolver modo parcial o completo."""

    paginas: int
    productos_por_pagina: int | None
    max_workers: int
    modo_completo: bool
    paginacion_sitio: dict[str, int] | None = None


def _url_pagina(numero: int) -> str:
    """URL del listado; la pagina 1 no lleva query ?page=."""
    if numero <= 1:
        return RAM_CATEGORIA_URL
    return f"{RAM_CATEGORIA_URL}?page={numero}"


def _resolver_config(
    *,
    productos_por_pagina: int | None,
    paginas: int | None,
    max_workers: int | None,
    modo_completo: bool,
    logger: logging.Logger,
) -> ConfigListado:
    """Ajusta paginas, limite por pagina e hilos segun el modo elegido."""
    if modo_completo:
        sesion = crear_sesion()
        html = obtener_html(sesion, RAM_CATEGORIA_URL, logger)
        paginacion = extraer_paginacion_categoria(html, logger)
        return ConfigListado(
            paginas=paginacion["total_paginas"],
            productos_por_pagina=None,
            max_workers=max_workers or min(RAM_MAX_WORKERS_LISTADO_COMPLETO, paginacion["total_paginas"]),
            modo_completo=True,
            paginacion_sitio=paginacion,
        )

    return ConfigListado(
        paginas=paginas or RAM_PAGINAS_LISTADO,
        productos_por_pagina=productos_por_pagina or RAM_PRODUCTOS_POR_PAGINA,
        max_workers=max_workers or RAM_MAX_WORKERS_LISTADO,
        modo_completo=False,
    )


# -----------------------------------------------------------------------------
# Extraccion por pagina
# -----------------------------------------------------------------------------


def _scrapear_pagina(numero: int, debug: bool) -> dict[str, Any]:
    """
    Descarga una pagina del listado y devuelve sus productos.

    Usa sesion propia para ser seguro bajo ThreadPoolExecutor.
    """
    logger = configurar_logger(f"listado_ram.pagina_{numero}", debug)
    url = _url_pagina(numero)
    sesion = crear_sesion()

    html = obtener_html(sesion, url, logger)
    productos = extraer_item_list(parsear_scripts_json_ld(html))

    for producto in productos:
        producto["pagina_origen"] = numero

    logger.info("Pagina %s: %s productos en %s", numero, len(productos), url)
    return {"pagina": numero, "url": url, "productos": productos, "total": len(productos)}


def _descargar_paginas_paralelo(
    config: ConfigListado,
    debug: bool,
    logger: logging.Logger,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Lanza un hilo por pagina y recopila resultados o errores."""
    resultados: list[dict[str, Any]] = []
    errores: list[str] = []
    workers = min(config.max_workers, config.paginas)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futuros = {
            pool.submit(_scrapear_pagina, n, debug): n
            for n in range(1, config.paginas + 1)
        }
        for futuro in as_completed(futuros):
            numero = futuros[futuro]
            try:
                resultados.append(futuro.result())
            except Exception as exc:
                mensaje = f"Pagina {numero}: {exc}"
                logger.error(mensaje)
                errores.append(mensaje)

    resultados.sort(key=lambda r: r["pagina"])
    return resultados, errores


# -----------------------------------------------------------------------------
# Catalogo final
# -----------------------------------------------------------------------------


def _seleccionar_de_pagina(
    productos: list[dict[str, Any]],
    limite: int | None,
    urls_vistas: set[str],
) -> list[dict[str, Any]]:
    """
    Toma hasta `limite` productos unicos de una pagina (None = todos).

    Las URLs ya vistas en paginas anteriores se omiten.
    """
    seleccion: list[dict[str, Any]] = []

    for item in ordenar_por_posicion_listado(productos):
        url = item.get("url")
        if not url or url in urls_vistas:
            continue
        urls_vistas.add(url)
        seleccion.append(item)
        if limite is not None and len(seleccion) >= limite:
            break

    return seleccion


def _construir_catalogo(productos_crudos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Anade ID estable y renombra campos al esquema de listado_ram.json."""
    total = len(productos_crudos)
    catalogo: list[dict[str, Any]] = []

    for indice, producto in enumerate(productos_crudos, start=1):
        catalogo.append(
            {
                "id": formatear_id_ram(indice, total),
                "nombre": producto.get("nombre"),
                "url": producto.get("url"),
                "precio_listado": producto.get("precio"),
                "valoracion_listado": producto.get("valoracion"),
                "num_opiniones_listado": producto.get("num_opiniones"),
                "sku": producto.get("sku"),
                "pagina_origen": producto.get("pagina_origen"),
                "posicion_listado": producto.get("posicion"),
            }
        )

    return catalogo


# -----------------------------------------------------------------------------
# Punto de entrada
# -----------------------------------------------------------------------------


def ejecutar_listado(
    productos_por_pagina: int | None = RAM_PRODUCTOS_POR_PAGINA,
    paginas: int | None = RAM_PAGINAS_LISTADO,
    max_workers: int | None = None,
    modo_completo: bool = False,
    debug: bool = False,
) -> dict[str, Any]:
    """
    Ejecuta el listado y persiste listado_ram.json.

    Ver ConfigListado y docstring del modulo para modos parcial y completo.
    """
    logger = configurar_logger("listado_ram", debug)
    config = _resolver_config(
        productos_por_pagina=productos_por_pagina,
        paginas=paginas,
        max_workers=max_workers,
        modo_completo=modo_completo,
        logger=logger,
    )

    etiqueta_limite = "todos" if config.productos_por_pagina is None else str(config.productos_por_pagina)
    estimado = (
        config.paginacion_sitio["total_productos"]
        if config.paginacion_sitio
        else config.paginas * (config.productos_por_pagina or 0)
    )

    logger.info(
        "Listado RAM%s: %s paginas, %s prod/pagina (~%s total), %s hilos",
        " [COMPLETO]" if config.modo_completo else "",
        config.paginas,
        etiqueta_limite,
        estimado,
        config.max_workers,
    )

    resultados, errores = _descargar_paginas_paralelo(config, debug, logger)

    urls_vistas: set[str] = set()
    productos_acumulados: list[dict[str, Any]] = []
    resumen_paginas: list[dict[str, Any]] = []

    for bloque in resultados:
        seleccion = _seleccionar_de_pagina(bloque["productos"], config.productos_por_pagina, urls_vistas)
        productos_acumulados.extend(seleccion)
        resumen_paginas.append(
            {
                "pagina": bloque["pagina"],
                "productos_disponibles": bloque["total"],
                "productos_guardados": len(seleccion),
            }
        )
        logger.info(
            "Pagina %s: %s guardados de %s detectados",
            bloque["pagina"],
            len(seleccion),
            bloque["total"],
        )

    catalogo = _construir_catalogo(productos_acumulados)

    metadata: dict[str, Any] = {
        "categoria": "memorias_ram",
        "fecha_extraccion": timestamp_utc(),
        "url_categoria": RAM_CATEGORIA_URL,
        "modo_completo": config.modo_completo,
        "paginas_exploradas": list(range(1, config.paginas + 1)),
        "paginas_procesadas_ok": [r["pagina"] for r in resultados],
        "productos_por_pagina": config.productos_por_pagina,
        "productos_objetivo_estimado": estimado,
        "total_productos_detectados": sum(r["total"] for r in resultados),
        "total_productos_guardados": len(catalogo),
        "resumen_por_pagina": resumen_paginas,
        "errores": errores,
    }
    if config.paginacion_sitio:
        metadata["paginacion_sitio"] = config.paginacion_sitio

    salida = {"metadata": metadata, "productos": catalogo}
    guardar_json(RAM_LISTADO_JSON, salida, logger)
    logger.info("Listado completado: %s productos -> %s", len(catalogo), RAM_LISTADO_JSON)
    return salida


if __name__ == "__main__":
    ejecutar_listado(debug=True)