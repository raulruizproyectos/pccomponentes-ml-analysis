"""Carga de los datos limpios de RAM en PostgreSQL."""

import json
from pathlib import Path

from database.inserciones_ram import (
    insertar_distribucion_valoraciones,
    insertar_especificaciones_ram,
    insertar_productos_ram,
    insertar_resenas_ram,
)


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_RAM_PROCESADA = RAIZ_PROYECTO / "data" / "procesados" / "ram"


def leer_json(nombre_archivo, directorio=None):
    directorio = directorio or RUTA_RAM_PROCESADA
    ruta = Path(directorio) / nombre_archivo

    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def preparar_datos_ram_desde_json(directorio=None):
    return {
        "productos": leer_json("productos_ram_limpios.json", directorio),
        "especificaciones": leer_json(
            "especificaciones_ram_limpias.json", directorio
        ),
        "distribuciones": leer_json(
            "distribucion_valoraciones_ram_limpia.json", directorio
        ),
        "resenas": leer_json("resenas_ram_limpias.json", directorio),
    }


def cargar_ram_a_postgresql(
    database_uri=None,
    dry_run=False,
    directorio_procesados=None,
):
    datos = preparar_datos_ram_desde_json(directorio_procesados)

    conteos = {
        nombre: len(registros)
        for nombre, registros in datos.items()
    }

    if dry_run:
        return conteos

    if not database_uri:
        raise ValueError("Falta la dirección de conexión a PostgreSQL")

    import psycopg

    with psycopg.connect(database_uri) as conn:
        insertar_productos_ram(conn, datos["productos"])
        insertar_especificaciones_ram(conn, datos["especificaciones"])
        insertar_distribucion_valoraciones(
            conn,
            datos["distribuciones"],
        )
        insertar_resenas_ram(conn, datos["resenas"])

        conn.commit()

    return conteos