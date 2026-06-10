"""
Scraper de DETALLE (ficha individual) de memorias RAM en PcComponentes.

Responsabilidad:
    Para cada producto del catálogo, descargar su página de ficha y extraer
    datos que no están (o están incompletos) en el listado:
      - Precio actualizado (puede haber ofertas)
      - Resumen de valoraciones + histograma de estrellas
      - Lista de reseñas individuales (muestra embebida en JSON-LD)
      - Especificaciones técnicas estructuradas (tipo DDR, capacidad,
        frecuencia, latencia, kit, compatibilidad...)

Características importantes de robustez:
    - Reanudación segura por URL (no por ID). Esto sobrevive a cambios
      de formato de ID (ram_001 → ram_0001) que hemos visto en el pasado.
    - Checkpoints cada N productos (configurable). Si hay bloqueo a mitad,
      el progreso ya está en disco.
    - Bloqueos reales (Cloudflare, captcha, 403/429, HTML muy corto...):
      guarda "interrumpido_bloqueo", imprime instrucciones y sale con 2.
    - Fichas sin datos (200 OK pero sin Product JSON-LD ni opiniones):
      se tratan como error por-producto → se añaden a "errores", se saltan
      y se continúa con el siguiente. No paran el scraper.
    - Nunca pierde trabajo previo.

Uso típico de reanudación:
    python ejecutar_scraper.py detalle --reanudar
    python ejecutar_scraper.py detalle --desde-cero   # ignora progreso previo
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any

from config.settings import (
    RAM_DETALLE_CHECKPOINT_CADA,
    RAM_DETALLE_DELAY_SECONDS,
    RAM_DETALLE_JSON,
    RAM_LISTADO_JSON,
)
from scrapers.utilidades import (
    BloqueoDetectadoError,
    cargar_json,
    combinar_resumen_opiniones,
    configurar_logger,
    crear_sesion,
    extraer_especificaciones_ram,
    extraer_opiniones_embebidas,
    extraer_producto_json_ld,
    extraer_resenas_de_producto_ld,
    guardar_json,
    obtener_html,
    parsear_scripts_json_ld,
    precio_desde_ofertas,
    timestamp_utc,
)

# Estados persistidos en metadata de detalle_ram.json
ESTADO_EN_PROGRESO = "en_progreso"
ESTADO_COMPLETADO = "completado"
ESTADO_BLOQUEO = "interrumpido_bloqueo"

COMANDO_REANUDAR = "python ejecutar_scraper.py detalle --reanudar"


# -----------------------------------------------------------------------------
# Salida por terminal ante bloqueo
# -----------------------------------------------------------------------------


def _avisar_bloqueo_en_terminal(
    error: BloqueoDetectadoError,
    producto_id: str,
    procesados: int,
    total: int,
    ruta_json: Path,
) -> None:
    """Mensaje visible en stderr con progreso y comando de reanudacion."""
    linea = "=" * 78
    pendientes = total - procesados

    print(f"\n{linea}", file=sys.stderr)
    print("  BLOQUEO DETECTADO - Scraper de detalle detenido", file=sys.stderr)
    print(linea, file=sys.stderr)
    print(f"  Motivo    : {error.motivo}", file=sys.stderr)
    print(f"  URL       : {error.url}", file=sys.stderr)
    print(f"  Producto  : {producto_id} (pendiente de guardar)", file=sys.stderr)
    print(f"  Progreso  : {procesados}/{total} completados", file=sys.stderr)
    print(f"  Pendientes: {pendientes}", file=sys.stderr)
    print(f"  Fichero   : {ruta_json}", file=sys.stderr)
    print(linea, file=sys.stderr)
    print("  Espera unos minutos y ejecuta:", file=sys.stderr)
    print(f"    {COMANDO_REANUDAR}", file=sys.stderr)
    print(linea, file=sys.stderr)
    print(file=sys.stderr)


# -----------------------------------------------------------------------------
# Extraccion de una ficha
# -----------------------------------------------------------------------------


def _extraer_ficha(
    entrada_catalogo: dict[str, Any],
    sesion,
    logger: logging.Logger,
    debug: bool,
) -> dict[str, Any]:
    """Descarga y normaliza una ficha de producto."""
    url = entrada_catalogo["url"]
    producto_id = entrada_catalogo["id"]

    logger.info("Extrayendo [%s]: %s", producto_id, url)
    html = obtener_html(sesion, url, logger, validar_ficha_producto=True)

    json_ld = parsear_scripts_json_ld(html)
    producto_ld = extraer_producto_json_ld(json_ld)
    opiniones_html = extraer_opiniones_embebidas(html, logger)

    nombre = entrada_catalogo.get("nombre")
    precio = entrada_catalogo.get("precio_listado")
    sku = entrada_catalogo.get("sku")

    if producto_ld:
        nombre = producto_ld.get("name") or nombre
        sku = producto_ld.get("sku") or sku
        if (precio_ld := precio_desde_ofertas(producto_ld)) is not None:
            precio = precio_ld

    opiniones = combinar_resumen_opiniones(producto_ld, opiniones_html, logger)

    # Reseñas individuales (muestra embebida en JSON-LD)
    resenas = extraer_resenas_de_producto_ld(producto_ld, logger)
    if resenas:
        opiniones = dict(opiniones)  # copia para no mutar el resumen base
        opiniones["resenas"] = resenas
        opiniones["resenas_extraidas"] = len(resenas)

    # Especificaciones técnicas RAM (a partir de nombre + HTML)
    especificaciones = extraer_especificaciones_ram(nombre, html, producto_ld, logger)

    # ------------------------------------------------------------------
    # Manejo de fichas sin datos de producto ni opiniones
    # (cambio de comportamiento solicitado por el usuario)
    #
    # Si el HTML se descargó correctamente (200, tamaño razonable, sin
    # patrones de Cloudflare/captcha/rate-limit), pero no contiene
    # JSON-LD de tipo Product ni payloads de reseñas/opiniones:
    #   - NO es un bloqueo de sesión/IP.
    #   - Casi siempre indica producto descatalogado, sin stock, o página
    #     servida sin los datos embebidos habituales.
    #   - Lo registramos como error recuperable (en la lista "errores" del
    #     JSON), incrementamos el contador de operaciones, guardamos
    #     checkpoint y pasamos al siguiente producto pendiente.
    #   - De esta forma un solo producto "raro" no para los 72 restantes.
    #
    # Solo los bloqueos reales (ver detectar_bloqueo_en_respuesta) lanzan
    # BloqueoDetectadoError y llaman a _registrar_bloqueo (SystemExit(2)).
    # ------------------------------------------------------------------
    if not producto_ld and len(resenas) == 0 and not (opiniones or {}).get("total_opiniones"):
        logger.warning(
            "[%s] Ficha sin datos de producto ni opiniones - se omite "
            "(posible producto descatalogado o sin reseñas disponibles). "
            "Continuando con el siguiente...",
            producto_id,
        )
        raise RuntimeError("ficha sin datos de producto ni opiniones (producto omitido)")

    if debug:
        logger.debug(
            "[%s] precio=%s media=%s opiniones=%s resenas_ld=%s specs=%s",
            producto_id,
            precio,
            opiniones.get("valoracion_media"),
            opiniones.get("total_opiniones"),
            len(resenas),
            {k: v for k, v in especificaciones.items() if v is not None},
        )

    return {
        "id": producto_id,
        "url": url,
        "nombre": nombre,
        "sku": sku,
        "precio": precio,
        "moneda": "EUR",
        "opiniones": opiniones,
        "resenas": resenas,
        "especificaciones": especificaciones,
    }


# -----------------------------------------------------------------------------
# Persistencia y reanudacion
# -----------------------------------------------------------------------------


def _armar_json_detalle(
    ruta_listado: Path,
    catalogo: list[dict[str, Any]],
    fichas: list[dict[str, Any]],
    errores: list[dict[str, str]],
    delay: float,
    reanudado: bool,
    *,
    estado: str = ESTADO_EN_PROGRESO,
    bloqueo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Estructura comun para checkpoints y resultado final."""
    metadata: dict[str, Any] = {
        "categoria": "memorias_ram",
        "fecha_extraccion": timestamp_utc(),
        "origen_listado": str(ruta_listado),
        "estado": estado,
        "total_productos": len(catalogo),
        "total_procesados_ok": len(fichas),
        "total_errores": len(errores),
        "total_pendientes": len(catalogo) - len(fichas),
        "delay_segundos": delay,
        "reanudado": reanudado,
        "ultimo_id_procesado": fichas[-1]["id"] if fichas else None,
    }
    if bloqueo:
        metadata["bloqueo"] = bloqueo

    return {"metadata": metadata, "productos": fichas, "errores": errores}


def _guardar_checkpoint(
    ruta_listado: Path,
    catalogo: list[dict[str, Any]],
    fichas: list[dict[str, Any]],
    errores: list[dict[str, str]],
    delay: float,
    reanudado: bool,
    logger: logging.Logger,
    *,
    estado: str = ESTADO_EN_PROGRESO,
    bloqueo: dict[str, Any] | None = None,
) -> None:
    datos = _armar_json_detalle(
        ruta_listado,
        catalogo,
        fichas,
        errores,
        delay,
        reanudado,
        estado=estado,
        bloqueo=bloqueo,
    )
    guardar_json(RAM_DETALLE_JSON, datos, logger)


def _cargar_progreso_previo(logger: logging.Logger) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Lee fichas y errores ya guardados en detalle_ram.json."""
    previo = cargar_json(RAM_DETALLE_JSON, logger)
    return list(previo.get("productos", [])), list(previo.get("errores", []))


def _pendientes_por_url(
    catalogo: list[dict[str, Any]],
    fichas_guardadas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Calcula qué productos del catálogo aún no tienen ficha procesada.

    Usamos la URL como clave (y no el ID) porque:
      - En el pasado los IDs cambiaron de formato (ram_001 vs ram_0001).
      - Una URL siempre identifica de forma única un producto en el sitio.
      - Permite reanudar incluso si regeneramos el listado con otro esquema de IDs.
    """
    urls_hechas = {f["url"] for f in fichas_guardadas if f.get("url")}
    return [p for p in catalogo if p.get("url") not in urls_hechas]


def _registrar_bloqueo(
    error: BloqueoDetectadoError,
    producto_id: str,
    ruta_listado: Path,
    catalogo: list[dict[str, Any]],
    fichas: list[dict[str, Any]],
    errores: list[dict[str, str]],
    delay: float,
    reanudado: bool,
    logger: logging.Logger,
) -> None:
    """Guarda progreso, imprime aviso y termina el proceso con codigo 2."""
    info_bloqueo = {
        "motivo": error.motivo,
        "url": error.url,
        "codigo_http": error.codigo_http,
        "bytes_html": error.bytes_html,
        "producto_id_interrumpido": producto_id,
        "fecha": timestamp_utc(),
    }
    _guardar_checkpoint(
        ruta_listado,
        catalogo,
        fichas,
        errores,
        delay,
        reanudado,
        logger,
        estado=ESTADO_BLOQUEO,
        bloqueo=info_bloqueo,
    )
    _avisar_bloqueo_en_terminal(error, producto_id, len(fichas), len(catalogo), RAM_DETALLE_JSON)
    logger.error("Interrumpido por bloqueo en %s", producto_id)
    raise SystemExit(2) from error


# -----------------------------------------------------------------------------
# Punto de entrada
# -----------------------------------------------------------------------------


def ejecutar_detalle(
    ruta_listado: str | None = None,
    delay_segundos: float = RAM_DETALLE_DELAY_SECONDS,
    reanudar: bool = False,
    desde_cero: bool = False,
    debug: bool = False,
) -> dict[str, Any]:
    """
    Procesa el catalogo de listado y escribe detalle_ram.json.

    Raises:
        SystemExit(2): Solo si se detecta un bloqueo real de PcComponentes
            (Cloudflare, rate-limit, etc.). Los productos individuales sin
            datos de producto/opiniones se saltan (se registran en "errores")
            y el proceso continúa.
    """
    logger = configurar_logger("detalle_ram", debug)
    ruta = RAM_LISTADO_JSON if ruta_listado is None else Path(ruta_listado)

    logger.info("Catalogo: %s", ruta)
    listado = cargar_json(ruta, logger)
    catalogo = listado.get("productos", [])

    if not catalogo:
        raise ValueError("El listado no contiene productos.")

    fichas: list[dict[str, Any]] = []
    errores: list[dict[str, str]] = []
    reanudado = False

    if not desde_cero and RAM_DETALLE_JSON.exists():
        fichas, errores = _cargar_progreso_previo(logger)
        if fichas:
            reanudar = True

    pendientes = _pendientes_por_url(catalogo, fichas)

    if reanudar and fichas:
        logger.info("Reanudando: %s hechas, %s pendientes", len(fichas), len(pendientes))
    elif desde_cero:
        logger.info("Detalle desde cero (sin usar progreso previo)")

    logger.info(
        "Pendientes: %s / %s (pausa %s s entre fichas)",
        len(pendientes),
        len(catalogo),
        delay_segundos,
    )

    if not pendientes:
        logger.info("Catalogo de detalle ya completo.")
        salida = _armar_json_detalle(
            ruta, catalogo, fichas, errores, delay_segundos, reanudado, estado=ESTADO_COMPLETADO
        )
        guardar_json(RAM_DETALLE_JSON, salida, logger)
        return salida

    sesion = crear_sesion()
    operaciones_desde_checkpoint = 0

    for indice, entrada in enumerate(pendientes):
        producto_id = entrada.get("id", "")

        try:
            fichas.append(_extraer_ficha(entrada, sesion, logger, debug))
            operaciones_desde_checkpoint += 1

        except BloqueoDetectadoError as error:
            _registrar_bloqueo(
                error,
                producto_id,
                ruta,
                catalogo,
                fichas,
                errores,
                delay_segundos,
                reanudado,
                logger,
            )

        except Exception as error:
            logger.error("Fallo en %s: %s", producto_id, error)
            errores.append(
                {"id": producto_id, "url": entrada.get("url", ""), "error": str(error)}
            )
            operaciones_desde_checkpoint += 1

        ultimo = indice == len(pendientes) - 1
        if operaciones_desde_checkpoint >= RAM_DETALLE_CHECKPOINT_CADA or ultimo:
            _guardar_checkpoint(
                ruta, catalogo, fichas, errores, delay_segundos, reanudado, logger
            )
            logger.info("Checkpoint: %s/%s", len(fichas), len(catalogo))
            operaciones_desde_checkpoint = 0

        if not ultimo and delay_segundos > 0:
            time.sleep(delay_segundos)

    salida = _armar_json_detalle(
        ruta, catalogo, fichas, errores, delay_segundos, reanudado, estado=ESTADO_COMPLETADO
    )
    guardar_json(RAM_DETALLE_JSON, salida, logger)
    logger.info("Detalle completado: %s/%s -> %s", len(fichas), len(catalogo), RAM_DETALLE_JSON)
    return salida


if __name__ == "__main__":
    ejecutar_detalle(debug=True)