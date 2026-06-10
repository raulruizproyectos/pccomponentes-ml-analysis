"""
Utilidades compartidas por los scrapers de PcComponentes.

Este módulo centraliza toda la lógica común para evitar duplicación entre
los scrapers de listado (categoría) y detalle (ficha de producto).

Responsabilidades principales:
    - Gestión robusta de peticiones HTTP con reintentos y detección agresiva
      de bloqueos reales (Cloudflare, captcha, rate-limit, HTML vacío o
      cortísimo, códigos 403/429/503). Lanza BloqueoDetectadoError.
    - Las fichas individuales que devuelven 200 pero sin Product JSON-LD
      ni datos de opiniones (posibles productos descatalogados) NO se
      tratan como bloqueo: se dejan pasar para manejo por-producto en el
      caller (se saltan y se registran en "errores").
    - Parseo de datos estructurados: JSON-LD (schema.org ItemList / Product),
      payloads embebidos de opiniones (React/JSON escapado en el HTML),
      y extracción de paginación.
    - Persistencia simple de JSON (listado_ram.json y detalle_ram.json)
      con metadata de fecha, estado, errores y reanudación.
    - Normalización de reseñas y especificaciones técnicas (específico de RAM
      por ahora).

Diseño clave:
    - Una Session requests por hilo en el listado paralelo (evita compartir
      estado de cookies/headers entre páginas).
    - Detección de bloqueo ANTES de raise_for_status para poder distinguir
      403/429 de "ficha sin datos".
    - Los datos de reseñas y specs completos viven en el JSON-LD de la ficha
      (hasta ~15 reseñas de muestra + aggregateRating). Las reseñas "todas"
      y la tabla de características completa suelen estar en JS renderizado,
      por lo que usamos heurísticos sobre el nombre del producto como fuente
      principal + fallback a HTML visible.

Usado por: listado_ram.py, detalle_ram.py (y en el futuro por los de GPUs).
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from config.settings import RAM_HTML_MINIMO_FICHA_BYTES, REQUEST_TIMEOUT_SECONDS

# =============================================================================
# Excepciones
# =============================================================================


class BloqueoDetectadoError(Exception):
    """
    Excepción específica para bloqueos / protecciones de PcComponentes.

    El scraper de detalle la captura para:
      - Guardar inmediatamente el checkpoint con el estado "interrumpido_bloqueo".
      - Imprimir un mensaje muy visible en stderr con el comando de reanudación.
      - Salir con código 2 (para que el CLI de ejecutar_scraper.py lo propague).

    Atributos públicos (se serializan en el JSON de detalle):
        motivo, url, codigo_http, bytes_html, (en caller: producto_id y fecha).
    """

    def __init__(
        self,
        motivo: str,
        url: str,
        codigo_http: int | None = None,
        bytes_html: int = 0,
    ) -> None:
        self.motivo = motivo
        self.url = url
        self.codigo_http = codigo_http
        self.bytes_html = bytes_html
        sufijo_http = f" (HTTP {codigo_http})" if codigo_http else ""
        super().__init__(
            f"Bloqueo detectado{sufijo_http} en {url}: {motivo} [{bytes_html} bytes]"
        )


# =============================================================================
# Constantes internas
# =============================================================================

# Cabeceras realistas de navegador. PcComponentes (y su WAF) rechaza con más
# frecuencia los User-Agent por defecto de requests / python.
CABECERAS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}

# HTTP status que casi siempre significan que nos han cortado el acceso.
CODIGOS_HTTP_BLOQUEO = frozenset({403, 429, 503})

# Patrones de texto que aparecen en páginas de Cloudflare / captcha / rate limit.
# Se buscan solo en los primeros 25k caracteres por rendimiento.
_PATRONES_TEXTO_BLOQUEO = tuple(
    re.compile(patron, re.IGNORECASE)
    for patron in (
        r"captcha",
        r"cloudflare",
        r"access denied",
        r"too many requests",
        r"rate limit",
        r"request blocked",
        r"verificaci[oó]n de seguridad",
        r"are you a robot",
        r"cf-browser-verification",
    )
)

# Regex para el payload de resumen de opiniones que inyecta React en el HTML
# (formato muy específico con comillas escapadas). Devuelve avg (0-10), recommend
# count y el objeto JSON del histograma de estrellas.
_REGEX_OPINIONES_HTML = re.compile(
    r'\\"avg\\":([\d.]+),\\"recommend\\":(\d+),\\"rating\\":(\{[^}]+\})',
    re.DOTALL,
)

# Regex para extraer información de paginación del HTML de la categoría.
# Prioridad en tiempo de ejecución: payload embebido > JSON-LD > texto visible.
_REGEX_TOTAL_PAGINAS = re.compile(r'\\"totalPages\\":(\d+)')
_REGEX_TOTAL_PRODUCTOS = re.compile(r'\\"totalProducts\\":(\d+)')
_REGEX_PAGINA_TEXTO = re.compile(r"P[aá]gina\s+1\s+de\s+(\d+)", re.IGNORECASE)

# Valor por defecto para el histograma cuando solo tenemos aggregateRating del LD.
DESGLOSE_ESTRELLAS_VACIO: dict[str, int] = {
    "estrellas_5": 0,
    "estrellas_4": 0,
    "estrellas_3": 0,
    "estrellas_2": 0,
    "estrellas_1": 0,
}


# =============================================================================
# Logging y HTTP
# =============================================================================


def configurar_logger(nombre: str, nivel_debug: bool = False) -> logging.Logger:
    """Devuelve un logger de consola; evita duplicar handlers en llamadas repetidas."""
    logger = logging.getLogger(nombre)
    if logger.handlers:
        return logger

    nivel = logging.DEBUG if nivel_debug else logging.INFO
    logger.setLevel(nivel)

    manejador = logging.StreamHandler()
    manejador.setLevel(nivel)
    manejador.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(manejador)
    logger.propagate = False
    return logger


def crear_sesion() -> requests.Session:
    """Sesion HTTP con cabeceras de navegador. Una sesion por hilo en listado paralelo."""
    sesion = requests.Session()
    sesion.headers.update(CABECERAS_HTTP)
    return sesion


def detectar_bloqueo_en_respuesta(
    url: str,
    codigo_http: int,
    html: str,
    *,
    validar_ficha_producto: bool = False,
) -> str | None:
    """
    Comprueba si la respuesta parece un BLOQUEO real de PcComponentes (WAF,
    Cloudflare, rate-limit, captcha, HTML vacío o muy corto, etc.).

    Returns:
        Texto con el motivo del bloqueo (se lanzará BloqueoDetectadoError), o
        None si la respuesta es plausible y debe procesarse.

    Notas de diseño (2026-06):
        - "ficha sin datos de producto ni opiniones" (ausencia de Product
          JSON-LD + opiniones) YA NO devuelve motivo de bloqueo.
        - Ese caso se trata como "producto individual sin datos" (posible
          descatalogado) y se maneja en el scraper de detalle como error
          recuperable por-producto (se añade a "errores" y se continúa).
        - Solo los indicadores de protección anti-bot detienen todo el run.
    """
    if codigo_http in CODIGOS_HTTP_BLOQUEO:
        return f"codigo HTTP {codigo_http}"

    if len(html) < RAM_HTML_MINIMO_FICHA_BYTES:
        return (
            f"HTML demasiado corto ({len(html)} bytes; "
            f"minimo {RAM_HTML_MINIMO_FICHA_BYTES})"
        )

    muestra_inicial = html[:25_000]
    for patron in _PATRONES_TEXTO_BLOQUEO:
        if patron.search(muestra_inicial):
            return f"contenido sospechoso ({patron.pattern})"

    if not validar_ficha_producto:
        return None

    # ------------------------------------------------------------------
    # Validación específica de ficha de producto (detalle).
    # IMPORTANTE (cambio de comportamiento):
    #   La ausencia de "Product" en JSON-LD + payload de opiniones + aggregateRating
    #   ya NO se considera "bloqueo".
    #
    #   Motivo: algunos productos legítimos (descatalogados, sin stock en
    #   ciertas regiones, o páginas servidas con HTML mínimo) devuelven 200
    #   pero sin los datos embebidos esperados.
    #
    #   Tratamiento:
    #     - Se descarga el HTML correctamente.
    #     - En _extraer_ficha (detalle_ram.py) se detecta que no hay datos
    #       útiles y se registra como error por-producto en la lista "errores".
    #     - Se salta ese producto y se continúa con el siguiente.
    #     - NO se levanta BloqueoDetectadoError, NO se para el scraper.
    #
    #   Solo se considera bloqueo real (y se para todo):
    #     - Códigos HTTP 403/429/503
    #     - HTML más corto que RAM_HTML_MINIMO_FICHA_BYTES
    #     - Patrones de Cloudflare, captcha, "too many requests", etc.
    # ------------------------------------------------------------------
    objetos_ld = parsear_scripts_json_ld(html)
    tiene_producto = any(_tipo_schema(obj) == "product" for obj in objetos_ld)
    tiene_opiniones = bool(_REGEX_OPINIONES_HTML.search(html))
    tiene_rating_ld = "aggregateRating" in html

    if not (tiene_producto or tiene_opiniones or tiene_rating_ld):
        # Ya no bloqueamos. Devolvemos None para que el HTML llegue al caller.
        # El caller (detalle_ram._extraer_ficha) detectará que no hay datos
        # útiles y lo registrará como error por-producto (se salta y continúa).
        return None

    return None


def obtener_html(
    sesion: requests.Session,
    url: str,
    logger: logging.Logger,
    *,
    reintentos: int = 3,
    pausa_reintento: float = 2.0,
    validar_ficha_producto: bool = False,
) -> str:
    """
    Descarga HTML con reintentos en fallos transitorios.

    Los bloqueos reales (Cloudflare, captcha, 403/429/503, HTML cortísimo,
    patrones de "rate limit"...) no se reintentan: se lanza
    BloqueoDetectadoError de inmediato para que el caller guarde checkpoint
    y pare limpio.

    La ausencia de datos de producto/opiniones en una ficha (200 OK pero sin
    JSON-LD Product ni payloads de reseñas) NO se considera bloqueo aquí.
    Se deja pasar el HTML para que el scraper de detalle lo maneje como
    "producto sin datos" (skipeable, se registra en errores y se sigue).
    """
    ultimo_error: Exception | None = None

    for intento in range(1, reintentos + 1):
        try:
            logger.debug("GET %s (intento %s/%s)", url, intento, reintentos)
            respuesta = sesion.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            html = respuesta.text
            codigo = respuesta.status_code

            motivo = detectar_bloqueo_en_respuesta(
                url,
                codigo,
                html,
                validar_ficha_producto=validar_ficha_producto,
            )
            if motivo:
                raise BloqueoDetectadoError(
                    motivo=motivo,
                    url=url,
                    codigo_http=codigo,
                    bytes_html=len(html),
                )

            respuesta.raise_for_status()
            logger.debug("HTML recibido: %s bytes", len(html))
            return html

        except BloqueoDetectadoError:
            raise

        except requests.HTTPError as error:
            codigo = error.response.status_code if error.response is not None else None
            if codigo in CODIGOS_HTTP_BLOQUEO:
                cuerpo = error.response.text if error.response is not None else ""
                raise BloqueoDetectadoError(
                    motivo=f"codigo HTTP {codigo}",
                    url=url,
                    codigo_http=codigo,
                    bytes_html=len(cuerpo),
                ) from error
            ultimo_error = error
            logger.warning("Error HTTP en %s: %s", url, error)
            if intento < reintentos:
                time.sleep(pausa_reintento)

        except requests.RequestException as error:
            ultimo_error = error
            logger.warning("Error de red en %s: %s", url, error)
            if intento < reintentos:
                time.sleep(pausa_reintento)

    assert ultimo_error is not None
    raise ultimo_error


# =============================================================================
# Persistencia y utilidades genericas
# =============================================================================


def guardar_json(ruta: Path, datos: dict[str, Any], logger: logging.Logger) -> None:
    """Escribe JSON con indentacion; crea directorios padre si no existen."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
    logger.info("JSON guardado en %s", ruta)


def cargar_json(ruta: Path, logger: logging.Logger) -> dict[str, Any]:
    """Lee un JSON existente; falla con mensaje claro si falta el fichero."""
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontro el fichero: {ruta}")
    with ruta.open("r", encoding="utf-8") as archivo:
        datos = json.load(archivo)
    logger.debug("JSON cargado desde %s", ruta)
    return datos


def timestamp_utc() -> str:
    """Marca temporal ISO-8601 en UTC para metadata de extraccion."""
    return datetime.now(timezone.utc).isoformat()


def formatear_id_ram(indice: int, total: int) -> str:
    """
    Genera IDs con ancho dinamico: ram_0001, ram_01672, etc.

    El ancho minimo es 4 digitos para mantener orden lexicografico estable.
    """
    ancho = max(4, len(str(total)))
    return f"ram_{indice:0{ancho}d}"


def ordenar_por_posicion_listado(productos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ordena productos segun la posicion del ItemList de schema.org."""
    return sorted(
        productos,
        key=lambda item: (item.get("posicion") is None, item.get("posicion") or 0),
    )


# =============================================================================
# Paginacion del listado de categoria
# =============================================================================


def extraer_paginacion_categoria(html: str, logger: logging.Logger) -> dict[str, int]:
    """
    Lee total de paginas y productos desde HTML de la categoria.

    Fuentes (por orden de preferencia): payload embebido, JSON-LD ItemList, texto visible.
    """
    total_paginas: int | None = None
    total_productos: int | None = None

    if coincidencia := _REGEX_TOTAL_PAGINAS.search(html):
        total_paginas = int(coincidencia.group(1))

    if coincidencia := _REGEX_TOTAL_PRODUCTOS.search(html):
        total_productos = int(coincidencia.group(1))

    if coincidencia := _REGEX_PAGINA_TEXTO.search(html):
        total_paginas = int(coincidencia.group(1))

    for objeto in parsear_scripts_json_ld(html):
        if _tipo_schema(objeto) == "itemlist" and objeto.get("numberOfItems") is not None:
            total_productos = int(objeto["numberOfItems"])

    if total_paginas is None:
        total_paginas = 1
        logger.warning("No se detecto total de paginas; se asumira 1.")

    if total_productos is None:
        total_productos = 0
        logger.warning("No se detecto total de productos en categoria.")

    logger.info(
        "Paginacion: %s paginas, %s productos",
        total_paginas,
        total_productos,
    )
    return {"total_paginas": total_paginas, "total_productos": total_productos}


# =============================================================================
# Parseo JSON-LD (schema.org)
# =============================================================================


def parsear_scripts_json_ld(html: str) -> list[dict[str, Any]]:
    """Extrae todos los objetos de scripts type=application/ld+json."""
    soup = BeautifulSoup(html, "lxml")
    objetos: list[dict[str, Any]] = []

    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            contenido = json.loads(script.string)
        except json.JSONDecodeError:
            continue

        if isinstance(contenido, list):
            objetos.extend(item for item in contenido if isinstance(item, dict))
        elif isinstance(contenido, dict):
            objetos.append(contenido)

    return objetos


def _tipo_schema(objeto: dict[str, Any]) -> str:
    """Normaliza @type de schema.org a minusculas para comparaciones."""
    return str(objeto.get("@type", "")).lower()


def extraer_item_list(json_ld: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convierte ItemList de schema.org en registros de producto del listado.

    Cada registro incluye datos utiles para el catalogo y para priorizar orden.
    """
    productos: list[dict[str, Any]] = []

    for objeto in json_ld:
        if _tipo_schema(objeto) != "itemlist":
            continue

        for elemento in objeto.get("itemListElement", []):
            item = elemento.get("item", {})
            if _tipo_schema(item) != "product":
                continue

            oferta = item.get("offers", {})
            rating = item.get("aggregateRating", {})
            precio_raw = oferta.get("price")

            productos.append(
                {
                    "nombre": item.get("name"),
                    "url": item.get("url"),
                    "precio": float(precio_raw) if precio_raw is not None else None,
                    "valoracion": (
                        float(rating["ratingValue"])
                        if rating.get("ratingValue") is not None
                        else None
                    ),
                    "num_opiniones": int(rating.get("ratingCount", 0) or 0),
                    "sku": item.get("sku"),
                    "posicion": elemento.get("position"),
                }
            )

    return productos


def extraer_producto_json_ld(json_ld: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Devuelve el primer bloque Product/product de una ficha de detalle."""
    for objeto in json_ld:
        if _tipo_schema(objeto) == "product":
            return objeto
    return None


def precio_desde_ofertas(producto_ld: dict[str, Any]) -> float | None:
    """
    Obtiene el precio principal desde offers o AggregateOffer.

    PcComponentes puede exponer Offer simple o AggregateOffer con sub-oferta.
    """
    ofertas = producto_ld.get("offers")
    if not isinstance(ofertas, dict):
        return None

    if (precio := ofertas.get("price")) is not None:
        return float(precio)

    sub_oferta = ofertas.get("offers")
    if isinstance(sub_oferta, dict) and sub_oferta.get("price") is not None:
        return float(sub_oferta["price"])

    if (precio_bajo := ofertas.get("lowPrice")) is not None:
        return float(precio_bajo)

    return None


# =============================================================================
# Opiniones y valoraciones
# =============================================================================


def extraer_opiniones_embebidas(
    html: str,
    logger: logging.Logger,
) -> dict[str, Any] | None:
    """
    Lee el resumen de opiniones del payload embebido en la ficha.

    Escala avg: 0-10 (se convierte a 0-5 para valoracion_media).
    Incluye recuento por estrellas del 1 al 5.
    """
    coincidencia = _REGEX_OPINIONES_HTML.search(html)
    if not coincidencia:
        logger.debug("Sin bloque embebido de opiniones en HTML")
        return None

    media_10 = float(coincidencia.group(1))
    recomendaciones = int(coincidencia.group(2))
    rating_json = coincidencia.group(3).replace('\\"', '"')
    distribucion = json.loads(rating_json)

    desglose = {
        "estrellas_5": int(distribucion.get("5", 0)),
        "estrellas_4": int(distribucion.get("4", 0)),
        "estrellas_3": int(distribucion.get("3", 0)),
        "estrellas_2": int(distribucion.get("2", 0)),
        "estrellas_1": int(distribucion.get("1", 0)),
    }

    return {
        "valoracion_media_10": media_10,
        "valoracion_media": round(media_10 / 2, 3),
        "recomendaciones": recomendaciones,
        "desglose_estrellas": desglose,
        "total_histograma": sum(desglose.values()),
    }


def combinar_resumen_opiniones(
    producto_ld: dict[str, Any] | None,
    opiniones_html: dict[str, Any] | None,
    logger: logging.Logger,
) -> dict[str, Any]:
    """
    Unifica opiniones desde JSON-LD y desde HTML embebido.

    El histograma por estrellas prioriza HTML porque JSON-LD suele omitirlo.
    """
    resumen: dict[str, Any] = {
        "total_opiniones": None,
        "total_resenas_con_texto": None,
        "valoracion_media": None,
        "porcentaje_recomendacion": None,
        "recomendaciones": None,
        "desglose_estrellas": dict(DESGLOSE_ESTRELLAS_VACIO),
        "fuente_desglose": None,
    }

    if producto_ld:
        rating = producto_ld.get("aggregateRating") or {}
        resumen["total_opiniones"] = int(rating.get("ratingCount", 0) or 0)
        resumen["total_resenas_con_texto"] = int(rating.get("reviewCount", 0) or 0)
        if rating.get("ratingValue") is not None:
            resumen["valoracion_media"] = float(rating["ratingValue"])

    if not opiniones_html:
        if resumen["total_opiniones"]:
            resumen["fuente_desglose"] = "solo_json_ld_sin_histograma"
            logger.debug("Sin histograma de estrellas en HTML")
        return resumen

    if resumen["valoracion_media"] is None:
        resumen["valoracion_media"] = opiniones_html["valoracion_media"]

    resumen["recomendaciones"] = opiniones_html["recomendaciones"]
    resumen["desglose_estrellas"] = opiniones_html["desglose_estrellas"]
    resumen["fuente_desglose"] = "html_embebido"

    if resumen["total_opiniones"] is None and opiniones_html["total_histograma"] > 0:
        resumen["total_opiniones"] = opiniones_html["total_histograma"]

    total = resumen["total_opiniones"]
    recomendaciones = resumen["recomendaciones"]
    if total and recomendaciones is not None:
        resumen["porcentaje_recomendacion"] = round(100 * recomendaciones / total, 2)

    return resumen


# =============================================================================
# Extracción de reseñas individuales (desde JSON-LD embebido en ficha)
# =============================================================================


def _normalizar_resena_ld(resena: dict[str, Any], logger: logging.Logger) -> dict[str, Any]:
    """
    Convierte un objeto Review del JSON-LD de schema.org al formato exacto
    que espera la tabla `resenas` de la base de datos.

    Limitaciones conocidas (por diseño del sitio):
        - opinion_verificada / opinion_destacada / likes / numero_respuestas
          normalmente solo aparecen en la interfaz de "Ver todas las opiniones"
          (cargada vía JS o fetch adicional). Aquí los dejamos en None.
        - Solo obtenemos las reseñas que PcComponentes decide incluir en el
          JSON-LD de la ficha (suele ser una muestra de las más recientes o
          destacadas, máximo ~15).
    """
    # author puede ser string o objeto Person
    author = resena.get("author") or {}
    if isinstance(author, dict):
        usuario = author.get("name")
    else:
        usuario = str(author) if author else None

    # reviewRating puede tener ratingValue como float o string
    rating = resena.get("reviewRating") or {}
    valoracion = None
    if isinstance(rating, dict):
        rv = rating.get("ratingValue")
        if rv is not None:
            try:
                valoracion = float(rv)
            except (TypeError, ValueError):
                pass

    # positiveNotes y negativeNotes vienen como ItemList de ListItem que
    # contienen un Comment con el texto. Los unimos con " | " para guardar
    # en una sola columna de texto.
    def _extraer_notas(notas: dict[str, Any] | None) -> str | None:
        if not isinstance(notas, dict):
            return None
        elems = notas.get("itemListElement") or []
        textos: list[str] = []
        for el in elems:
            if not isinstance(el, dict):
                continue
            item = el.get("item") or {}
            if isinstance(item, dict):
                t = item.get("text")
                if t:
                    textos.append(str(t).strip())
        if textos:
            return " | ".join(textos)
        return None

    pros = _extraer_notas(resena.get("positiveNotes"))
    contras = _extraer_notas(resena.get("negativeNotes"))

    texto = resena.get("reviewBody")
    if texto:
        texto = str(texto).strip()

    fecha = resena.get("datePublished")
    if fecha:
        # Conservamos el ISO completo; el ETL o consultas pueden truncarlo.
        fecha = str(fecha)

    # Puede ser lista de imágenes o un solo objeto
    imagenes = resena.get("image") or []
    tiene_imagen = bool(imagenes) if isinstance(imagenes, (list, tuple)) else bool(imagenes)

    return {
        "usuario": usuario,
        "valoracion": valoracion,
        "opinion_verificada": None,   # Requiere sección de opiniones JS
        "opinion_destacada": None,
        "fecha_resena_texto": fecha,
        "variante_modelo": None,      # A veces viene en la UI como "Versión RGB"
        "color": None,
        "texto_resena": texto or None,
        "pros": pros,
        "contras": contras,
        "likes": None,
        "numero_respuestas": None,
        "tiene_imagen": tiene_imagen,
    }


def extraer_resenas_de_producto_ld(
    producto_ld: dict[str, Any] | None,
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """
    Punto de entrada público para obtener reseñas individuales de una ficha.

    Busca la clave "review" dentro del objeto Product del JSON-LD.
    Normaliza cada una usando el esquema de la tabla de base de datos.

    Returns:
        Lista (posiblemente vacía) de diccionarios listos para insertar en
        la tabla `resenas`. Nunca lanza excepción (los fallos individuales
        se loguean en DEBUG).

    Importante:
        Esta es la fuente "fácil" y ya disponible durante el scrape normal.
        Para el 100% de las reseñas de un producto habría que navegar la
        paginación de opiniones o llamar al endpoint interno que usa la web.
    """
    if not producto_ld:
        return []

    raw_reviews = producto_ld.get("review") or []
    if isinstance(raw_reviews, dict):
        raw_reviews = [raw_reviews]

    resenas: list[dict[str, Any]] = []
    for r in raw_reviews:
        if not isinstance(r, dict):
            continue
        try:
            norm = _normalizar_resena_ld(r, logger)
            resenas.append(norm)
        except Exception as exc:
            logger.debug("Fallo normalizando una resena LD: %s", exc)

    if resenas:
        logger.debug("Extraidas %s resenas desde JSON-LD", len(resenas))
    return resenas


# =============================================================================
# Extracción de especificaciones técnicas de memorias RAM
# =============================================================================


def extraer_especificaciones_ram(
    nombre: str | None,
    html: str | None = None,
    producto_ld: dict[str, Any] | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """
    Parser heurístico de especificaciones de memorias RAM.

    Estrategia (por limitaciones del sitio):
      1. Fuente principal = el propio `nombre` del producto. Los nombres en
         PcComponentes son extremadamente descriptivos y siguen patrones
         muy consistentes ("Corsair Vengeance RGB DDR5 6000MHz 32GB 2x16GB CL36...").
      2. Enriquecimiento secundario desde el HTML visible (bloque "wrapficha"
         o bullets de características destacadas) para voltaje y algún texto
         de compatibilidad.
      3. Fallback muy ligero al JSON-LD (description).

    NO intentamos scrapear la tabla completa de "Especificaciones técnicas"
    porque suele estar renderizada por JavaScript y no aparece en el HTML
    estático que descargamos. Si en el futuro se necesita el 100% de campos,
    habría que usar Playwright o extraer el gran blob de datos de la app.

    Campos devueltos (alineados con el TODO de Dani y la tabla
    especificaciones_ram):
    """
    specs: dict[str, Any] = {
        "tipo_memoria": None,
        "capacidad_gb": None,
        "kit": None,
        "num_modulos": None,
        "capacidad_por_modulo_gb": None,
        "frecuencia_mhz": None,
        "latencia_cl": None,
        "voltaje": None,
        "diseno": None,
        "compatibilidad": None,
        "color": None,
        "disipador": None,
        "fuente": "nombre",
    }

    texto = (nombre or "").strip()
    if not texto and html:
        # fallback muy basico del html si no hay nombre
        try:
            soup = BeautifulSoup(html, "html.parser")
            h1 = soup.find("h1")
            if h1:
                texto = h1.get_text(" ", strip=True)
        except Exception:
            pass

    if not texto:
        return specs

    t = texto

    # --- Tipo de memoria (el más fiable del nombre)
    m = re.search(r"\b(DDR[345])\b", t, re.IGNORECASE)
    if m:
        specs["tipo_memoria"] = m.group(1).upper()

    # --- Frecuencia (buscamos el patrón más común "6000 MHz")
    m = re.search(r"(\d{3,5})\s*MHz", t, re.IGNORECASE)
    if m:
        try:
            specs["frecuencia_mhz"] = int(m.group(1))
        except ValueError:
            pass

    # --- Latencia CAS (CL30, CL36...)
    m = re.search(r"\bCL\s*(\d{1,2})\b", t, re.IGNORECASE)
    if m:
        try:
            specs["latencia_cl"] = int(m.group(1))
        except ValueError:
            pass

    # --- Capacidad y formato de kit (la parte más importante para RAM)
    # Patrones habituales:
    #   "32 GB 2x16GB", "32GB (2 x 16GB)", "16GB", "64GB"
    m = re.search(
        r"(\d+)\s*(?:GB|G)\s*(?:\(?\s*(\d+)\s*[xX]\s*(\d+)\s*(?:GB|G)?\s*\)?)?",
        t,
        re.IGNORECASE,
    )
    if m:
        total = int(m.group(1))
        specs["capacidad_gb"] = total
        if m.group(2) and m.group(3):
            mods = int(m.group(2))
            por = int(m.group(3))
            specs["num_modulos"] = mods
            specs["capacidad_por_modulo_gb"] = por
            specs["kit"] = f"{mods}x{por}GB"
        else:
            specs["num_modulos"] = 1
            specs["capacidad_por_modulo_gb"] = total
            specs["kit"] = "single"

    # Refuerzo por si el patrón anterior no capturó un "2x..." suelto
    if specs["num_modulos"] is None:
        m2 = re.search(r"(\d+)\s*[xX]\s*(\d+)\s*(?:GB|G)", t, re.IGNORECASE)
        if m2 and specs["capacidad_gb"]:
            try:
                mods = int(m2.group(1))
                specs["num_modulos"] = mods
                specs["kit"] = f"{mods}x{specs['capacidad_por_modulo_gb'] or (specs['capacidad_gb']//mods)}GB"
            except Exception:
                pass

    # --- Color (suele ir al final del nombre)
    m = re.search(r"\b(Negra|Negro|Blanca|Blanco|Gris|RGB|Plata)\b", t, re.IGNORECASE)
    if m:
        specs["color"] = m.group(1).capitalize()

    # --- Perfiles de overclock / compatibilidad con plataformas
    comps: list[str] = []
    if re.search(r"\bXMP\b", t, re.IGNORECASE):
        comps.append("XMP")
    if re.search(r"\bEXPO\b", t, re.IGNORECASE):
        comps.append("EXPO")
    if re.search(r"\bRyzen\b|AMD", t, re.IGNORECASE):
        comps.append("AMD")
    if re.search(r"\bIntel\b", t, re.IGNORECASE):
        comps.append("Intel")
    if comps:
        specs["compatibilidad"] = ", ".join(sorted(set(comps)))

    # --- Presencia de disipador / heatsink
    if re.search(r"disipador|heatsink|rgb", t, re.IGNORECASE):
        specs["disipador"] = True

    # --- Factor de forma (importante para portátiles vs sobremesa)
    if re.search(r"\bSO-?DIMM\b|SODIMM|laptop|portatil|notebook", t, re.IGNORECASE):
        specs["diseno"] = "SODIMM"
    elif re.search(r"\bDIMM\b|desktop|pc", t, re.IGNORECASE):
        specs["diseno"] = "DIMM"

    # --- Enriquecimiento desde HTML visible (sin depender de JS)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        wrap = soup.find("div", class_=re.compile(r"wrapficha|destacad|caracter", re.I))
        if wrap:
            bullets = wrap.get_text(" | ", strip=True)
            # Voltaje aparece a veces como "1.35V" en los bullets destacados
            mv = re.search(r"(\d\.\d{1,2})\s*V", bullets, re.IGNORECASE)
            if mv:
                try:
                    specs["voltaje"] = float(mv.group(1))
                except ValueError:
                    pass
            if not specs.get("compatibilidad"):
                if "XMP" in bullets or "EXPO" in bullets:
                    specs["compatibilidad"] = "XMP/EXPO"
            specs["fuente"] = "nombre+html"

    # --- Último recurso: description del JSON-LD
    if producto_ld and specs["fuente"] == "nombre":
        desc = producto_ld.get("description") or ""
        if "SODIMM" in desc or "SO-DIMM" in desc:
            specs["diseno"] = "SODIMM"
        specs["fuente"] = "nombre+ld"

    return specs
