"""
Convenciones de rutas S3 del proyecto.

Replica la estructura local para cada categoría:
    data/brutos/<slug>/        -> s3://<bucket>/brutos/<slug>/
    data/procesados/<slug>/    -> s3://<bucket>/procesados/<slug>/
"""

from __future__ import annotations

from dataclasses import dataclass

from aws.categorias import (
    CategoriaPipeline,
    clave_s3_brutos,
    clave_s3_procesados,
    identificar_categoria_por_clave_s3,
    obtener_categoria,
)


def clave_s3_brutos_ram(nombre_archivo: str) -> str:
    return clave_s3_brutos(obtener_categoria("ram"), nombre_archivo)


def clave_s3_procesados_ram(nombre_archivo: str) -> str:
    return clave_s3_procesados(obtener_categoria("ram"), nombre_archivo)


def clave_s3_brutos_gpu(nombre_archivo: str) -> str:
    return clave_s3_brutos(obtener_categoria("tarjetas_graficas"), nombre_archivo)


def clave_s3_procesados_gpu(nombre_archivo: str) -> str:
    return clave_s3_procesados(obtener_categoria("tarjetas_graficas"), nombre_archivo)


@dataclass(frozen=True)
class ObjetoS3:
    bucket: str
    clave: str


def parsear_registro_evento_s3(registro: dict) -> ObjetoS3:
    """Extrae bucket y clave de un registro S3 de un evento Lambda."""
    return ObjetoS3(
        bucket=registro["s3"]["bucket"]["name"],
        clave=registro["s3"]["object"]["key"],
    )


def es_clave_ram_brutos(clave: str) -> bool:
    categoria = obtener_categoria("ram")
    return clave.startswith(f"{categoria.prefijo_brutos_s3}/")


def es_clave_ram_procesados(clave: str) -> bool:
    categoria = obtener_categoria("ram")
    return clave.startswith(f"{categoria.prefijo_procesados_s3}/")


def es_clave_s3_soportada(clave: str) -> bool:
    return identificar_categoria_por_clave_s3(clave) is not None