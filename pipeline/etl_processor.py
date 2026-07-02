"""
Pipeline ETL (Extract-Transform-Load) del proyecto.

Actualmente implementado solo para el flujo de memorias RAM.

Flujo típico:
    1. Los scrapers producen JSON "bruto" en data/brutos/ram/
    2. Esta capa lee esos JSON, prepara tuplas limpias y las inserta
       en PostgreSQL usando las funciones de database/inserciones.py
    3. (Futuro) Transformaciones más avanzadas: normalización de nombres
       de modelo, enriquecimiento de specs, deduplicación de reseñas, etc.

Uso recomendado:
    from pipeline.etl_processor import cargar_ram_a_postgresql
    cargar_ram_a_postgresql(os.environ["DATABASE_URL"], dry_run=False)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config.settings import (
    GPU_PROCESADOS_ARCHIVOS,
    RAM_DETALLE_JSON,
    RAM_LISTADO_JSON,
    RAM_PROCESADOS_ARCHIVOS,
)
from database.inserciones import (
    insertar_distribucion_valoraciones,
    insertar_especificaciones_gpu,
    insertar_productos_gpu,
    insertar_productos_ram,
    insertar_especificaciones_ram,
    insertar_resenas_ram,
)


def preparar_datos_ram_desde_json(
    ruta_listado: Path | None = None,
    ruta_detalle: Path | None = None,
) -> dict[str, list[tuple]]:
    """
    Lee los JSONs de RAM y prepara las secuencias de tuplas listas para executemany.
    Devuelve dict con 'productos', 'especificaciones', 'resenas'.
    """
    ruta_listado = ruta_listado or RAM_LISTADO_JSON
    ruta_detalle = ruta_detalle or RAM_DETALLE_JSON

    with open(ruta_listado, encoding="utf-8") as f:
        listado = json.load(f)
    with open(ruta_detalle, encoding="utf-8") as f:
        detalle = json.load(f)

    cat = {p["id"]: p for p in listado.get("productos", [])}
    productos_tuples: list[tuple] = []
    specs_tuples: list[tuple] = []
    resenas_tuples: list[tuple] = []

    for ficha in detalle.get("productos", []):
        pid = ficha.get("id")
        base = cat.get(pid, {})
        nombre = ficha.get("nombre") or base.get("nombre", "")
        precio = ficha.get("precio") or base.get("precio_listado")
        sku = ficha.get("sku")
        ops = ficha.get("opiniones") or {}
        esp = ficha.get("especificaciones") or {}

        productos_tuples.append(
            (
                pid,
                ficha.get("url"),
                nombre,
                sku,
                precio,
                ops.get("valoracion_media"),
                ops.get("total_opiniones"),
                ops.get("porcentaje_recomendacion"),
                "ram_scraper_v1",
            )
        )

        specs_tuples.append(
            (
                pid,
                esp.get("tipo_memoria"),
                esp.get("capacidad_gb"),
                esp.get("kit"),
                esp.get("num_modulos"),
                esp.get("capacidad_por_modulo_gb"),
                esp.get("frecuencia_mhz"),
                esp.get("latencia_cl"),
                esp.get("voltaje"),
                esp.get("diseno"),
                esp.get("compatibilidad"),
                esp.get("color"),
                esp.get("disipador"),
                esp.get("fuente"),
            )
        )

        for r in (ficha.get("resenas") or []):
            resenas_tuples.append(
                (
                    pid,
                    r.get("usuario"),
                    r.get("valoracion"),
                    r.get("opinion_verificada"),
                    r.get("opinion_destacada"),
                    r.get("fecha_resena_texto"),
                    r.get("variante_modelo"),
                    r.get("color"),
                    r.get("texto_resena"),
                    r.get("pros"),
                    r.get("contras"),
                    r.get("likes"),
                    r.get("numero_respuestas"),
                    r.get("tiene_imagen"),
                )
            )

    return {
        "productos": productos_tuples,
        "especificaciones": specs_tuples,
        "resenas": resenas_tuples,
    }


def preparar_datos_ram_desde_procesados(
    directorio_procesados: Path | None = None,
    *,
    rutas: dict[str, Path] | None = None,
) -> dict[str, list[tuple]]:
    """
    Lee los JSON limpios generados por pipeline/limpieza_ram.py
    y prepara tuplas listas para PostgreSQL.
    """
    if rutas is None:
        if directorio_procesados is None:
            rutas = RAM_PROCESADOS_ARCHIVOS
        else:
            rutas = {
                nombre: directorio_procesados / archivo.name
                for nombre, archivo in RAM_PROCESADOS_ARCHIVOS.items()
            }

    with open(rutas["productos"], encoding="utf-8") as f:
        productos = json.load(f)
    with open(rutas["especificaciones"], encoding="utf-8") as f:
        especificaciones = json.load(f)
    with open(rutas["distribuciones"], encoding="utf-8") as f:
        distribuciones = json.load(f)
    with open(rutas["resenas"], encoding="utf-8") as f:
        resenas = json.load(f)

    productos_tuples = [
        (
            p["producto_id"],
            p.get("url"),
            p.get("nombre"),
            p.get("sku"),
            p.get("precio"),
            p.get("valoracion_media"),
            p.get("total_opiniones"),
            p.get("porcentaje_recomendacion"),
            p.get("fuente"),
        )
        for p in productos
    ]

    specs_tuples = [
        (
            e["producto_id"],
            e.get("tipo_memoria"),
            e.get("capacidad_gb"),
            e.get("kit"),
            e.get("num_modulos"),
            e.get("capacidad_por_modulo_gb"),
            e.get("frecuencia_mhz"),
            e.get("latencia_cl"),
            e.get("voltaje"),
            e.get("diseno"),
            e.get("compatibilidad"),
            e.get("color"),
            e.get("disipador"),
            e.get("fuente"),
        )
        for e in especificaciones
    ]

    distribuciones_tuples = [
        (
            d["producto_id"],
            d.get("estrellas_5", 0),
            d.get("estrellas_4", 0),
            d.get("estrellas_3", 0),
            d.get("estrellas_2", 0),
            d.get("estrellas_1", 0),
        )
        for d in distribuciones
    ]

    resenas_tuples = [
        (
            r["producto_id"],
            None,
            r.get("valoracion"),
            r.get("texto_resena"),
            r.get("pros"),
            r.get("contras"),
        )
        for r in resenas
    ]

    return {
        "productos": productos_tuples,
        "especificaciones": specs_tuples,
        "distribuciones": distribuciones_tuples,
        "resenas": resenas_tuples,
    }


def cargar_ram_procesados_a_postgresql(
    database_uri: str,
    *,
    directorio_procesados: Path | None = None,
    rutas: dict[str, Path] | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """Carga los JSON procesados de RAM a PostgreSQL."""
    datos = preparar_datos_ram_desde_procesados(directorio_procesados, rutas=rutas)
    print(
        f"Preparados (procesados): {len(datos['productos'])} productos, "
        f"{len(datos['especificaciones'])} specs, "
        f"{len(datos['distribuciones'])} distribuciones, "
        f"{len(datos['resenas'])} resenas"
    )

    if dry_run:
        print("DRY RUN activado, no se inserta nada.")
        return {k: len(v) for k, v in datos.items()}

    import psycopg

    with psycopg.connect(database_uri) as conn:
        print("Conectado. Insertando datos procesados...")
        if datos["productos"]:
            insertar_productos_ram(conn, datos["productos"])
        if datos["especificaciones"]:
            insertar_especificaciones_ram(conn, datos["especificaciones"])
        if datos["distribuciones"]:
            insertar_distribucion_valoraciones(conn, datos["distribuciones"])
        if datos["resenas"]:
            insertar_resenas_ram(conn, datos["resenas"])
        print("Carga completada.")

    return {k: len(v) for k, v in datos.items()}


def preparar_datos_gpu_desde_procesados(
    directorio_procesados: Path | None = None,
    *,
    rutas: dict[str, Path] | None = None,
) -> dict[str, list[tuple]]:
    """Lee los JSON limpios de tarjetas gráficas y prepara tuplas para PostgreSQL."""
    if rutas is None:
        if directorio_procesados is None:
            rutas = GPU_PROCESADOS_ARCHIVOS
        else:
            rutas = {
                nombre: directorio_procesados / archivo.name
                for nombre, archivo in GPU_PROCESADOS_ARCHIVOS.items()
            }

    for nombre, ruta in rutas.items():
        if not Path(ruta).is_file():
            raise FileNotFoundError(
                f"Falta el fichero procesado de GPU ({nombre}): {ruta}"
            )

    with open(rutas["productos"], encoding="utf-8") as f:
        productos = json.load(f)
    with open(rutas["especificaciones"], encoding="utf-8") as f:
        especificaciones = json.load(f)
    with open(rutas["distribuciones"], encoding="utf-8") as f:
        distribuciones = json.load(f)
    with open(rutas["resenas"], encoding="utf-8") as f:
        resenas = json.load(f)

    productos_tuples = [
        (
            p["producto_id"],
            p.get("url"),
            p.get("nombre"),
            p.get("sku"),
            p.get("precio"),
            p.get("valoracion_media"),
            p.get("total_opiniones"),
            p.get("porcentaje_recomendacion"),
            p.get("fuente", "pccomponentes_gpu"),
        )
        for p in productos
    ]

    specs_tuples = [
        (
            e["producto_id"],
            e.get("gpu"),
            e.get("memoria_vram"),
            e.get("tipo_memoria"),
            e.get("bus_memoria"),
            e.get("ancho_banda_memoria"),
            e.get("velocidad_memoria"),
            e.get("reloj_base"),
            e.get("reloj_boost"),
            e.get("salidas_video"),
            e.get("resolucion_maxima"),
        )
        for e in especificaciones
    ]

    distribuciones_tuples = [
        (
            d["producto_id"],
            d.get("estrellas_5", 0),
            d.get("estrellas_4", 0),
            d.get("estrellas_3", 0),
            d.get("estrellas_2", 0),
            d.get("estrellas_1", 0),
        )
        for d in distribuciones
    ]

    resenas_tuples = [
        (
            r["producto_id"],
            None,
            r.get("valoracion"),
            r.get("texto_resena"),
            r.get("pros"),
            r.get("contras"),
        )
        for r in resenas
    ]

    return {
        "productos": productos_tuples,
        "especificaciones": specs_tuples,
        "distribuciones": distribuciones_tuples,
        "resenas": resenas_tuples,
    }


def cargar_gpu_procesados_a_postgresql(
    database_uri: str,
    *,
    directorio_procesados: Path | None = None,
    rutas: dict[str, Path] | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """Carga los JSON procesados de tarjetas gráficas a PostgreSQL."""
    datos = preparar_datos_gpu_desde_procesados(directorio_procesados, rutas=rutas)
    print(
        f"Preparados GPU (procesados): {len(datos['productos'])} productos, "
        f"{len(datos['especificaciones'])} specs, "
        f"{len(datos['distribuciones'])} distribuciones, "
        f"{len(datos['resenas'])} resenas"
    )

    if dry_run:
        print("DRY RUN activado, no se inserta nada.")
        return {k: len(v) for k, v in datos.items()}

    import psycopg

    with psycopg.connect(database_uri) as conn:
        print("Conectado. Insertando datos GPU procesados...")
        if datos["productos"]:
            insertar_productos_gpu(conn, datos["productos"])
        if datos["especificaciones"]:
            insertar_especificaciones_gpu(conn, datos["especificaciones"])
        if datos["distribuciones"]:
            insertar_distribucion_valoraciones(conn, datos["distribuciones"])
        if datos["resenas"]:
            insertar_resenas_ram(conn, datos["resenas"])
        print("Carga GPU completada.")

    return {k: len(v) for k, v in datos.items()}


def cargar_ram_a_postgresql(database_uri: str, *, dry_run: bool = False) -> dict[str, int]:
    """
    Prepara y carga (o dry-run) los datos RAM actuales a la DB.
    Requiere que las tablas productos, especificaciones_ram y resenas existan.
    """
    import psycopg

    datos = preparar_datos_ram_desde_json()
    print(
        f"Preparados: {len(datos['productos'])} productos, "
        f"{len(datos['especificaciones'])} specs, "
        f"{len(datos['resenas'])} resenas"
    )

    if dry_run:
        print("DRY RUN activado, no se inserta nada.")
        return {k: len(v) for k, v in datos.items()}

    with psycopg.connect(database_uri) as conn:
        print("Conectado. Insertando...")
        if datos["productos"]:
            insertar_productos_ram(conn, datos["productos"])
        if datos["especificaciones"]:
            insertar_especificaciones_ram(conn, datos["especificaciones"])
        if datos["resenas"]:
            insertar_resenas_ram(conn, datos["resenas"])
        print("Carga completada.")

    return {k: len(v) for k, v in datos.items()}


def procesar_datos_brutos():
    """Entrada principal del pipeline (por ahora solo RAM)."""
    # En uso real: cargar config, llamar a cargar_ram_a_postgresql(os.environ["DATABASE_URL"])
    raise NotImplementedError(
        "Usa cargar_ram_a_postgresql(database_uri) o el script CLI cuando la DB esté lista. "
        "Ver pipeline/etl_processor.py y notebooks/03-04."
    )
