# Carga de los datos limpios de GPU en PostgreSQL.

import json
from pathlib import Path

from database.inserciones_gpu import (
    insertar_distribucion_valoraciones_gpu,
    insertar_especificaciones_gpu,
    insertar_productos_gpu,
)


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_GPU_PROCESADA = RAIZ_PROYECTO / "data" / "procesados" / "tarjetas_graficas"


def leer_json(nombre_archivo, directorio=None):
    directorio = directorio or RUTA_GPU_PROCESADA
    ruta = Path(directorio) / nombre_archivo

    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def preparar_datos_gpu_desde_json(directorio=None):
    return {
        "productos": leer_json("productos_tarjetas_graficas_limpios.json", directorio),
        "especificaciones": leer_json(
            "especificaciones_tarjetas_graficas_limpias.json",
            directorio,
        ),
        "distribuciones": leer_json(
            "distribucion_valoraciones_tarjetas_graficas_limpia.json",
            directorio,
        ),
    }


def cargar_gpu_a_postgresql(
    database_uri=None,
    dry_run=False,
    directorio_procesados=None,
):
    datos = preparar_datos_gpu_desde_json(directorio_procesados)

    conteos = {
        nombre: len(registros)
        for nombre, registros in datos.items()
    }

    if dry_run:
        return conteos

    if not database_uri:
        raise ValueError("Falta la direccion de conexion a PostgreSQL")

    import psycopg

    with psycopg.connect(database_uri) as conn:
        insertar_productos_gpu(conn, datos["productos"])
        insertar_especificaciones_gpu(conn, datos["especificaciones"])
        insertar_distribucion_valoraciones_gpu(conn, datos["distribuciones"])

        conn.commit()

    return conteos