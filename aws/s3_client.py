"""
Cliente S3 para subir y descargar los JSON del pipeline.

Soporta todas las categorías definidas en config.settings.PIPELINE_CATEGORIAS.
"""

from __future__ import annotations

from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from aws.categorias import (
    CategoriaPipeline,
    archivos_procesados_etl,
    clave_s3_brutos,
    clave_s3_procesados,
    listar_categorias,
    obtener_categoria,
    resolver_categorias,
)
from config.settings import AWS_REGION, AWS_S3_BUCKET


class ClienteS3:
    def __init__(
        self,
        *,
        bucket: str | None = None,
        region: str | None = None,
    ):
        self.bucket = bucket or AWS_S3_BUCKET
        self.region = region or AWS_REGION

        if not self.bucket:
            raise ValueError(
                "Falta AWS_S3_BUCKET. Configúralo en .env o como variable de entorno."
            )

        self._cliente = boto3.client("s3", region_name=self.region)

    def subir_archivo(self, ruta_local: Path, clave_s3: str) -> str:
        ruta_local = Path(ruta_local)
        if not ruta_local.is_file():
            raise FileNotFoundError(f"No existe el fichero local: {ruta_local}")

        self._cliente.upload_file(
            str(ruta_local),
            self.bucket,
            clave_s3,
            ExtraArgs={"ContentType": "application/json"},
        )
        return f"s3://{self.bucket}/{clave_s3}"

    def descargar_archivo(self, clave_s3: str, ruta_destino: Path) -> Path:
        ruta_destino = Path(ruta_destino)
        ruta_destino.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._cliente.download_file(self.bucket, clave_s3, str(ruta_destino))
        except ClientError as error:
            codigo = error.response["Error"].get("Code", "")
            if codigo in {"404", "NoSuchKey", "NotFound"}:
                raise FileNotFoundError(
                    f"No existe en S3: s3://{self.bucket}/{clave_s3}"
                ) from error
            raise
        return ruta_destino

    def existe(self, clave_s3: str) -> bool:
        try:
            self._cliente.head_object(Bucket=self.bucket, Key=clave_s3)
            return True
        except ClientError as error:
            if error.response["Error"]["Code"] == "404":
                return False
            raise

    def subir_conjunto(
        self,
        categoria: CategoriaPipeline,
        archivos: dict[str, Path],
        *,
        tipo: str,
        omitir_faltantes: bool = False,
    ) -> list[str]:
        subidos = []
        generador_clave = clave_s3_brutos if tipo == "brutos" else clave_s3_procesados

        for nombre, ruta in archivos.items():
            if not ruta.is_file():
                mensaje = f"[{categoria.nombre}] Falta {tipo}.{nombre}: {ruta}"
                if omitir_faltantes:
                    print(f"Omitido: {mensaje}")
                    continue
                raise FileNotFoundError(mensaje)

            clave = generador_clave(categoria, ruta.name)
            uri = self.subir_archivo(ruta, clave)
            subidos.append(uri)
            print(f"Subido [{categoria.nombre}] {nombre}: {uri}")

        return subidos

    def subir_brutos(
        self,
        categoria: CategoriaPipeline,
        *,
        omitir_faltantes: bool = False,
    ) -> list[str]:
        return self.subir_conjunto(
            categoria,
            categoria.brutos,
            tipo="brutos",
            omitir_faltantes=omitir_faltantes,
        )

    def subir_procesados(
        self,
        categoria: CategoriaPipeline,
        *,
        omitir_faltantes: bool = False,
    ) -> list[str]:
        return self.subir_conjunto(
            categoria,
            categoria.procesados,
            tipo="procesados",
            omitir_faltantes=omitir_faltantes,
        )

    def descargar_conjunto(
        self,
        categoria: CategoriaPipeline,
        archivos: dict[str, Path],
        directorio_destino: Path,
        *,
        tipo: str,
    ) -> dict[str, Path]:
        destino = Path(directorio_destino) / categoria.slug
        destino.mkdir(parents=True, exist_ok=True)
        generador_clave = clave_s3_brutos if tipo == "brutos" else clave_s3_procesados
        descargados = {}

        for nombre, ruta in archivos.items():
            clave = generador_clave(categoria, ruta.name)
            ruta_local = destino / ruta.name
            self.descargar_archivo(clave, ruta_local)
            descargados[nombre] = ruta_local

        return descargados

    def descargar_brutos(
        self,
        categoria: CategoriaPipeline,
        directorio_destino: Path,
    ) -> dict[str, Path]:
        return self.descargar_conjunto(
            categoria,
            categoria.brutos,
            directorio_destino,
            tipo="brutos",
        )

    def descargar_procesados(
        self,
        categoria: CategoriaPipeline,
        directorio_destino: Path,
    ) -> dict[str, Path]:
        return self.descargar_conjunto(
            categoria,
            categoria.procesados,
            directorio_destino,
            tipo="procesados",
        )

    def descargar_procesados_etl(
        self,
        categoria: CategoriaPipeline,
        directorio_destino: Path,
    ) -> dict[str, Path]:
        return self.descargar_conjunto(
            categoria,
            archivos_procesados_etl(categoria),
            directorio_destino,
            tipo="procesados",
        )

    def subir_categorias(
        self,
        seleccion: str = "todas",
        *,
        tipo: str = "todo",
        omitir_faltantes: bool = True,
    ) -> dict[str, list[str]]:
        resultados: dict[str, list[str]] = {}

        for categoria in resolver_categorias(seleccion):
            subidos: list[str] = []
            if tipo in ("brutos", "todo"):
                subidos.extend(
                    self.subir_brutos(categoria, omitir_faltantes=omitir_faltantes)
                )
            if tipo in ("procesados", "todo"):
                subidos.extend(
                    self.subir_procesados(categoria, omitir_faltantes=omitir_faltantes)
                )
            resultados[categoria.nombre] = subidos

        return resultados

    # Compatibilidad con la API anterior centrada en RAM
    def subir_ram_brutos(self, *, omitir_faltantes: bool = False) -> list[str]:
        return self.subir_brutos(obtener_categoria("ram"), omitir_faltantes=omitir_faltantes)

    def subir_ram_procesados(self, *, omitir_faltantes: bool = False) -> list[str]:
        return self.subir_procesados(
            obtener_categoria("ram"),
            omitir_faltantes=omitir_faltantes,
        )

    def descargar_ram_brutos(self, directorio_destino: Path) -> dict[str, Path]:
        return self.descargar_brutos(obtener_categoria("ram"), directorio_destino)

    def descargar_ram_procesados(self, directorio_destino: Path) -> dict[str, Path]:
        return self.descargar_procesados(obtener_categoria("ram"), directorio_destino)