"""
Registro de categorías soportadas por el pipeline AWS.

Cada categoría replica la misma estructura local:
    data/brutos/<slug>/
    data/procesados/<slug>/
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Callable

from config.settings import PIPELINE_CATEGORIAS


@dataclass(frozen=True)
class CategoriaPipeline:
    nombre: str
    slug: str
    categoria_db: str
    modulo_limpieza: str
    brutos: dict[str, Path]
    procesados: dict[str, Path]
    lista: bool

    @property
    def prefijo_brutos_s3(self) -> str:
        return f"brutos/{self.slug}"

    @property
    def prefijo_procesados_s3(self) -> str:
        return f"procesados/{self.slug}"


def obtener_categoria(nombre: str) -> CategoriaPipeline:
    if nombre not in PIPELINE_CATEGORIAS:
        disponibles = ", ".join(PIPELINE_CATEGORIAS)
        raise ValueError(f"Categoría desconocida: {nombre}. Disponibles: {disponibles}")

    config = PIPELINE_CATEGORIAS[nombre]
    return CategoriaPipeline(
        nombre=nombre,
        slug=config["slug"],
        categoria_db=config["categoria_db"],
        modulo_limpieza=config["modulo_limpieza"],
        brutos=config["brutos"],
        procesados=config["procesados"],
        lista=config["lista"],
    )


def listar_categorias() -> list[CategoriaPipeline]:
    return [obtener_categoria(nombre) for nombre in PIPELINE_CATEGORIAS]


def resolver_categorias(seleccion: str) -> list[CategoriaPipeline]:
    if seleccion == "todas":
        return listar_categorias()
    return [obtener_categoria(seleccion)]


def identificar_categoria_por_clave_s3(clave: str) -> CategoriaPipeline | None:
    for categoria in listar_categorias():
        if clave.startswith(f"{categoria.prefijo_brutos_s3}/"):
            return categoria
        if clave.startswith(f"{categoria.prefijo_procesados_s3}/"):
            return categoria
    return None


def es_clave_brutos(clave: str, categoria: CategoriaPipeline) -> bool:
    return clave.startswith(f"{categoria.prefijo_brutos_s3}/")


def es_clave_procesados(clave: str, categoria: CategoriaPipeline) -> bool:
    return clave.startswith(f"{categoria.prefijo_procesados_s3}/")


def clave_s3_brutos(categoria: CategoriaPipeline, nombre_archivo: str) -> str:
    return f"{categoria.prefijo_brutos_s3}/{nombre_archivo}"


def clave_s3_procesados(categoria: CategoriaPipeline, nombre_archivo: str) -> str:
    return f"{categoria.prefijo_procesados_s3}/{nombre_archivo}"


def importar_modulo_limpieza(categoria: CategoriaPipeline):
    return import_module(categoria.modulo_limpieza)


def obtener_cargador_etl(categoria: CategoriaPipeline) -> Callable:
    from pipeline import etl_processor

    if categoria.nombre == "ram":
        return etl_processor.cargar_ram_procesados_a_postgresql
    if categoria.nombre == "tarjetas_graficas":
        return etl_processor.cargar_gpu_procesados_a_postgresql

    raise ValueError(f"Sin cargador ETL para la categoría: {categoria.nombre}")