"""
Orquestación del pipeline AWS por categoría (RAM + tarjetas gráficas).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from aws.categorias import (
    CategoriaPipeline,
    es_clave_brutos,
    es_clave_procesados,
    identificar_categoria_por_clave_s3,
    importar_modulo_limpieza,
    obtener_cargador_etl,
    obtener_categoria,
)
from aws.s3_client import ClienteS3


def ejecutar_limpieza_local(
    categoria: CategoriaPipeline,
    *,
    rutas_brutos: dict[str, Path] | None = None,
    directorio_salida: Path | None = None,
) -> Path:
    limpieza = importar_modulo_limpieza(categoria)

    if rutas_brutos:
        if categoria.lista:
            limpieza.RUTA_LISTADO = rutas_brutos["listado"]
            limpieza.RUTA_DETALLE = rutas_brutos["detalle"]
        else:
            limpieza.RUTA_DATOS = rutas_brutos["dataset"]

    directorio_procesados = directorio_salida or categoria.procesados["productos"].parent
    limpieza.RUTA_SALIDA = directorio_procesados

    datos = limpieza.preparar_datos_limpios()
    if hasattr(limpieza, "validar_resultados"):
        limpieza.validar_resultados(datos)

    nombres_salida = {
        "productos": categoria.procesados["productos"].name,
        "especificaciones": categoria.procesados["especificaciones"].name,
        "distribuciones": categoria.procesados["distribuciones"].name,
        "resenas": categoria.procesados["resenas"].name,
    }

    for clave, nombre_archivo in nombres_salida.items():
        limpieza.guardar_json(datos[clave], directorio_procesados / nombre_archivo)

    return directorio_procesados


def ejecutar_etl_local(
    categoria: CategoriaPipeline,
    database_url: str,
    *,
    directorio_procesados: Path | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    cargador = obtener_cargador_etl(categoria)
    return cargador(
        database_url,
        directorio_procesados=directorio_procesados,
        dry_run=dry_run,
    )


def ejecutar_pipeline_local(
    categoria: CategoriaPipeline,
    database_url: str,
    *,
    dry_run: bool = False,
) -> dict[str, int]:
    directorio_procesados = ejecutar_limpieza_local(categoria)
    return ejecutar_etl_local(
        categoria,
        database_url,
        directorio_procesados=directorio_procesados,
        dry_run=dry_run,
    )


def procesar_objeto_s3(bucket: str, clave: str, database_url: str) -> dict:
    if clave.endswith(".keep"):
        return {
            "clave": clave,
            "estado": "omitido",
            "motivo": "marcador de prefijo",
        }

    categoria = identificar_categoria_por_clave_s3(clave)
    if categoria is None:
        return {
            "clave": clave,
            "estado": "omitido",
            "motivo": "prefijo no soportado",
        }

    cliente = ClienteS3(bucket=bucket)

    with tempfile.TemporaryDirectory(prefix="pcc-ml-") as tmp:
        base = Path(tmp)

        if es_clave_brutos(clave, categoria):
            rutas = cliente.descargar_brutos(categoria, base)
            directorio_procesados = ejecutar_limpieza_local(
                categoria,
                rutas_brutos=rutas,
                directorio_salida=base / "procesados" / categoria.slug,
            )
        elif es_clave_procesados(clave, categoria):
            cliente.descargar_procesados_etl(categoria, base / "procesados")
            directorio_procesados = base / "procesados" / categoria.slug
        else:
            return {
                "clave": clave,
                "categoria": categoria.nombre,
                "estado": "omitido",
                "motivo": "tipo de objeto no reconocido",
            }

        try:
            resultado = ejecutar_etl_local(
                categoria,
                database_url,
                directorio_procesados=directorio_procesados,
                dry_run=False,
            )
        except Exception as error:
            mensaje = str(error)
            if "duplicate key" in mensaje.lower():
                return {
                    "clave": clave,
                    "categoria": categoria.nombre,
                    "estado": "omitido",
                    "motivo": "datos ya cargados en PostgreSQL",
                    "detalle": mensaje,
                }
            raise

        return {
            "clave": clave,
            "categoria": categoria.nombre,
            "estado": "completado",
            "carga": resultado,
        }


def resumen_disponibilidad_local() -> dict[str, dict[str, bool]]:
    resumen = {}

    for categoria in [obtener_categoria("ram"), obtener_categoria("tarjetas_graficas")]:
        resumen[categoria.nombre] = {
            "lista": categoria.lista,
            "brutos": {nombre: ruta.is_file() for nombre, ruta in categoria.brutos.items()},
            "procesados": {
                nombre: ruta.is_file() for nombre, ruta in categoria.procesados.items()
            },
        }

    return resumen