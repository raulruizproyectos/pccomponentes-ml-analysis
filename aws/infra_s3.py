"""
Aprovisionamiento del bucket S3 del proyecto.

Crea el bucket, aplica configuración de seguridad básica y deja
los prefijos esperados por el pipeline:

    brutos/ram/
    brutos/tarjetas_graficas/
    procesados/ram/
    procesados/tarjetas_graficas/
"""

from __future__ import annotations

from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError

from aws.categorias import listar_categorias
from config.settings import AWS_REGION, AWS_S3_BUCKET


PREFIJOS_PIPELINE = tuple(
    f"brutos/{categoria.slug}/" for categoria in listar_categorias()
) + tuple(
    f"procesados/{categoria.slug}/" for categoria in listar_categorias()
)


@dataclass
class ResultadoInfraS3:
    bucket: str
    region: str
    creado: bool
    prefijos: list[str]
    mensaje: str


def _cliente_s3(region: str | None = None):
    return boto3.client("s3", region_name=region or AWS_REGION)


def bucket_existe(bucket: str, region: str | None = None) -> bool:
    cliente = _cliente_s3(region)
    try:
        cliente.head_bucket(Bucket=bucket)
        return True
    except ClientError as error:
        codigo = error.response["Error"].get("Code", "")
        if codigo in {"404", "NoSuchBucket", "NotFound"}:
            return False
        raise


def crear_bucket(bucket: str, region: str | None = None) -> bool:
    region = region or AWS_REGION
    cliente = _cliente_s3(region)

    if bucket_existe(bucket, region):
        return False

    parametros = {"Bucket": bucket}
    if region != "us-east-1":
        parametros["CreateBucketConfiguration"] = {"LocationConstraint": region}

    cliente.create_bucket(**parametros)
    return True


def configurar_seguridad_bucket(bucket: str, region: str | None = None) -> None:
    cliente = _cliente_s3(region)

    cliente.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )

    cliente.put_bucket_encryption(
        Bucket=bucket,
        ServerSideEncryptionConfiguration={
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256",
                    }
                }
            ]
        },
    )

    cliente.put_bucket_versioning(
        Bucket=bucket,
        VersioningConfiguration={"Status": "Enabled"},
    )


def crear_prefijos(bucket: str, prefijos: list[str] | None = None, region: str | None = None) -> list[str]:
    cliente = _cliente_s3(region)
    prefijos = prefijos or list(PREFIJOS_PIPELINE)
    creados = []

    for prefijo in prefijos:
        clave = f"{prefijo}.keep"
        cliente.put_object(
            Bucket=bucket,
            Key=clave,
            Body=b"",
            ContentType="application/octet-stream",
        )
        creados.append(prefijo)

    return creados


def verificar_bucket(bucket: str | None = None, region: str | None = None) -> dict:
    bucket = bucket or AWS_S3_BUCKET
    region = region or AWS_REGION
    cliente = _cliente_s3(region)

    if not bucket:
        raise ValueError("Falta AWS_S3_BUCKET.")

    existe = bucket_existe(bucket, region)
    resultado = {
        "bucket": bucket,
        "region": region,
        "existe": existe,
        "prefijos_pipeline": list(PREFIJOS_PIPELINE),
        "prefijos_presentes": [],
    }

    if not existe:
        return resultado

    paginator = cliente.get_paginator("list_objects_v2")
    prefijos_encontrados = set()

    for pagina in paginator.paginate(Bucket=bucket, Delimiter="/"):
        for prefijo in pagina.get("CommonPrefixes", []):
            prefijos_encontrados.add(prefijo["Prefix"])

    for prefijo_pipeline in PREFIJOS_PIPELINE:
        if prefijo_pipeline in prefijos_encontrados:
            resultado["prefijos_presentes"].append(prefijo_pipeline)

    return resultado


def aprovisionar_bucket(
    bucket: str | None = None,
    region: str | None = None,
    *,
    forzar_prefijos: bool = False,
) -> ResultadoInfraS3:
    bucket = bucket or AWS_S3_BUCKET
    region = region or AWS_REGION

    if not bucket:
        raise ValueError(
            "Falta AWS_S3_BUCKET. Configúralo en .env antes de crear el bucket."
        )

    creado = crear_bucket(bucket, region)
    configurar_seguridad_bucket(bucket, region)

    prefijos = []
    if creado or forzar_prefijos:
        prefijos = crear_prefijos(bucket, region=region)

    if creado:
        mensaje = f"Bucket creado y configurado: s3://{bucket}/"
    else:
        mensaje = f"El bucket ya existía. Seguridad revisada: s3://{bucket}/"
        if forzar_prefijos:
            mensaje += " Prefijos regenerados."

    return ResultadoInfraS3(
        bucket=bucket,
        region=region,
        creado=creado,
        prefijos=prefijos,
        mensaje=mensaje,
    )