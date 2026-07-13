"""
Aprovisionamiento de AWS Lambda para el pipeline ETL (S3 -> PostgreSQL).

Flujo:
    1. Empaqueta código + dependencias Linux (psycopg) en un ZIP.
    2. Crea/actualiza rol IAM, función Lambda y permisos S3.
    3. Activa Lambda cuando termina la subida de datos procesados.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from config.settings import AWS_REGION, AWS_S3_BUCKET

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = PROJECT_ROOT / "build" / "lambda"
PACKAGE_ZIP = PROJECT_ROOT / "build" / "lambda_package.zip"
REQUIREMENTS_LAMBDA = Path(__file__).resolve().parent / "requirements-lambda.txt"
POLITICA_ROL = Path(__file__).resolve().parent / "politica_iam_lambda_rol.json"

LAMBDA_FUNCTION_NAME = "pccomponentes-ml-etl"
LAMBDA_ROLE_NAME = "pccomponentes-ml-lambda-etl-role"
LAMBDA_HANDLER = "aws.lambda_handler.handler"
LAMBDA_RUNTIME = "python3.12"
LAMBDA_TIMEOUT = 300
LAMBDA_MEMORY = 512

PAQUETES_PROYECTO = ("aws", "config", "database", "pipeline")


@dataclass
class ResultadoDespliegueLambda:
    funcion: str
    region: str
    rol_arn: str
    funcion_arn: str
    paquete: str
    notificaciones_s3: list[str]
    mensaje: str


def _cliente_lambda(region: str | None = None):
    return boto3.client("lambda", region_name=region or AWS_REGION)


def _cliente_iam(region: str | None = None):
    return boto3.client("iam", region_name=region or AWS_REGION)


def _cliente_s3(region: str | None = None):
    return boto3.client("s3", region_name=region or AWS_REGION)


def _cliente_sts(region: str | None = None):
    return boto3.client("sts", region_name=region or AWS_REGION)


def empaquetar_lambda(*, destino: Path | None = None) -> Path:
    """Genera el ZIP de despliegue con wheels Linux compatibles con Lambda."""
    destino = destino or PACKAGE_ZIP
    destino.parent.mkdir(parents=True, exist_ok=True)

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(REQUIREMENTS_LAMBDA),
            "-t",
            str(BUILD_DIR),
            "--platform",
            "manylinux2014_x86_64",
            "--implementation",
            "cp",
            "--python-version",
            "3.12",
            "--only-binary",
            ":all:",
            "--upgrade",
        ],
        check=True,
    )

    for nombre_paquete in PAQUETES_PROYECTO:
        origen = PROJECT_ROOT / nombre_paquete
        if not origen.is_dir():
            raise FileNotFoundError(f"No existe el paquete del proyecto: {origen}")
        shutil.copytree(
            origen,
            BUILD_DIR / nombre_paquete,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".gitkeep"),
        )

    if destino.exists():
        destino.unlink()

    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as archivo_zip:
        for fichero in BUILD_DIR.rglob("*"):
            if fichero.is_file():
                archivo_zip.write(fichero, fichero.relative_to(BUILD_DIR))

    return destino


def _politica_rol_lambda(bucket: str) -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                "Resource": "arn:aws:logs:*:*:*",
            },
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:ListBucket"],
                "Resource": [
                    f"arn:aws:s3:::{bucket}",
                    f"arn:aws:s3:::{bucket}/*",
                ],
            },
        ],
    }


def _asegurar_rol_lambda(
    *,
    bucket: str,
    region: str | None = None,
) -> str:
    iam = _cliente_iam(region)
    trust_policy = json.loads(POLITICA_ROL.read_text(encoding="utf-8"))

    try:
        respuesta = iam.get_role(RoleName=LAMBDA_ROLE_NAME)
        rol_arn = respuesta["Role"]["Arn"]
    except ClientError as error:
        if error.response["Error"]["Code"] != "NoSuchEntity":
            raise
        respuesta = iam.create_role(
            RoleName=LAMBDA_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Rol para Lambda ETL pccomponentes-ml-analysis",
        )
        rol_arn = respuesta["Role"]["Arn"]

    iam.put_role_policy(
        RoleName=LAMBDA_ROLE_NAME,
        PolicyName="pccomponentes-ml-lambda-inline",
        PolicyDocument=json.dumps(_politica_rol_lambda(bucket)),
    )

    return rol_arn


def _asegurar_funcion_lambda(
    *,
    rol_arn: str,
    paquete: Path,
    database_url: str,
    bucket: str,
    region: str | None = None,
) -> str:
    lambda_client = _cliente_lambda(region)
    region = region or AWS_REGION
    codigo_zip = paquete.read_bytes()

    variables = {
        "DATABASE_URL": database_url,
        "AWS_S3_BUCKET": bucket,
        "AWS_REGION": region,
    }

    try:
        lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
        existe = True
    except ClientError as error:
        if error.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
        existe = False

    if existe:
        lambda_client.update_function_code(
            FunctionName=LAMBDA_FUNCTION_NAME,
            ZipFile=codigo_zip,
        )
        lambda_client.update_function_configuration(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Role=rol_arn,
            Handler=LAMBDA_HANDLER,
            Runtime=LAMBDA_RUNTIME,
            Timeout=LAMBDA_TIMEOUT,
            MemorySize=LAMBDA_MEMORY,
            Environment={"Variables": variables},
        )
    else:
        lambda_client.create_function(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Runtime=LAMBDA_RUNTIME,
            Role=rol_arn,
            Handler=LAMBDA_HANDLER,
            Code={"ZipFile": codigo_zip},
            Timeout=LAMBDA_TIMEOUT,
            MemorySize=LAMBDA_MEMORY,
            Environment={"Variables": variables},
            Description="ETL S3 -> PostgreSQL para RAM y tarjetas gráficas",
        )

    respuesta = lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
    return respuesta["Configuration"]["FunctionArn"]


def _permiso_s3_invocar_lambda(
    *,
    bucket: str,
    funcion_arn: str,
    region: str | None = None,
) -> None:
    lambda_client = _cliente_lambda(region)
    cuenta = _cliente_sts(region).get_caller_identity()["Account"]
    statement_id = f"s3-invoke-{bucket}"

    try:
        lambda_client.add_permission(
            FunctionName=LAMBDA_FUNCTION_NAME,
            StatementId=statement_id,
            Action="lambda:InvokeFunction",
            Principal="s3.amazonaws.com",
            SourceArn=f"arn:aws:s3:::{bucket}",
            SourceAccount=cuenta,
        )
    except ClientError as error:
        if error.response["Error"]["Code"] != "ResourceConflictException":
            raise


def _crear_reglas_notificacion_s3(funcion_arn: str) -> list[dict]:
    """Crea una regla por categoría usando el último fichero de la subida."""
    from aws.categorias import listar_categorias

    reglas = []

    for categoria in listar_categorias():
        prefijo = f"procesados/{categoria.slug}/"
        archivo_final = categoria.procesados["resenas"].name
        reglas.append(
            {
                "Id": f"etl-procesados-{categoria.slug}",
                "LambdaFunctionArn": funcion_arn,
                "Events": ["s3:ObjectCreated:*"],
                "Filter": {
                    "Key": {
                        "FilterRules": [
                            {"Name": "prefix", "Value": prefijo},
                            {"Name": "suffix", "Value": archivo_final},
                        ]
                    }
                },
            }
        )

    return reglas


def _configurar_notificaciones_s3(
    *,
    bucket: str,
    funcion_arn: str,
    region: str | None = None,
) -> list[str]:
    s3 = _cliente_s3(region)

    try:
        configuracion_actual = s3.get_bucket_notification_configuration(Bucket=bucket)
    except ClientError:
        configuracion_actual = {}

    configuracion_actual.pop("ResponseMetadata", None)

    reglas_lambda = [
        regla
        for regla in configuracion_actual.get("LambdaFunctionConfigurations", [])
        if regla.get("LambdaFunctionArn") != funcion_arn
    ]

    nuevas_reglas = _crear_reglas_notificacion_s3(funcion_arn)

    configuracion_actual["LambdaFunctionConfigurations"] = reglas_lambda + nuevas_reglas
    s3.put_bucket_notification_configuration(
        Bucket=bucket,
        NotificationConfiguration=configuracion_actual,
    )

    return [regla["Id"] for regla in nuevas_reglas]


def desplegar_lambda(
    *,
    database_url: str,
    bucket: str | None = None,
    region: str | None = None,
    empaquetar: bool = True,
) -> ResultadoDespliegueLambda:
    bucket = bucket or AWS_S3_BUCKET
    region = region or AWS_REGION

    if not bucket:
        raise ValueError("Falta AWS_S3_BUCKET.")
    if not database_url:
        raise ValueError("Falta DATABASE_URL para la variable de entorno de Lambda.")

    paquete = empaquetar_lambda() if empaquetar else PACKAGE_ZIP
    if not paquete.is_file():
        raise FileNotFoundError(f"No existe el paquete Lambda: {paquete}")

    rol_arn = _asegurar_rol_lambda(bucket=bucket, region=region)
    funcion_arn = _asegurar_funcion_lambda(
        rol_arn=rol_arn,
        paquete=paquete,
        database_url=database_url,
        bucket=bucket,
        region=region,
    )
    _permiso_s3_invocar_lambda(bucket=bucket, funcion_arn=funcion_arn, region=region)
    notificaciones = _configurar_notificaciones_s3(
        bucket=bucket,
        funcion_arn=funcion_arn,
        region=region,
    )

    return ResultadoDespliegueLambda(
        funcion=LAMBDA_FUNCTION_NAME,
        region=region,
        rol_arn=rol_arn,
        funcion_arn=funcion_arn,
        paquete=str(paquete),
        notificaciones_s3=notificaciones,
        mensaje=(
            f"Lambda desplegada: {LAMBDA_FUNCTION_NAME}. "
            f"Trigger S3 activo con {len(notificaciones)} reglas."
        ),
    )


def verificar_lambda(
    *,
    bucket: str | None = None,
    region: str | None = None,
) -> dict:
    bucket = bucket or AWS_S3_BUCKET
    region = region or AWS_REGION
    lambda_client = _cliente_lambda(region)
    resultado = {
        "funcion": LAMBDA_FUNCTION_NAME,
        "region": region,
        "bucket": bucket,
        "existe": False,
        "handler": LAMBDA_HANDLER,
        "runtime": LAMBDA_RUNTIME,
    }

    try:
        respuesta = lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
        config = respuesta["Configuration"]
        resultado.update(
            {
                "existe": True,
                "arn": config["FunctionArn"],
                "estado": config.get("State"),
                "ultima_modificacion": config.get("LastModified"),
                "timeout": config.get("Timeout"),
                "memoria_mb": config.get("MemorySize"),
                "variables_entorno": list(
                    config.get("Environment", {}).get("Variables", {}).keys()
                ),
            }
        )
    except ClientError as error:
        if error.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
        resultado["motivo"] = "La función Lambda no existe todavía."

    if bucket:
        try:
            notificaciones = _cliente_s3(region).get_bucket_notification_configuration(
                Bucket=bucket
            )
            reglas = notificaciones.get("LambdaFunctionConfigurations", [])
            resultado["notificaciones_s3"] = [
                {
                    "id": regla.get("Id"),
                    "prefijo": next(
                        (
                            filtro["Value"]
                            for filtro in regla.get("Filter", {})
                            .get("Key", {})
                            .get("FilterRules", [])
                            if filtro.get("Name") == "prefix"
                        ),
                        None,
                    ),
                    "sufijo": next(
                        (
                            filtro["Value"]
                            for filtro in regla.get("Filter", {})
                            .get("Key", {})
                            .get("FilterRules", [])
                            if filtro.get("Name") == "suffix"
                        ),
                        None,
                    ),
                }
                for regla in reglas
            ]
        except ClientError as error:
            resultado["notificaciones_s3_error"] = str(error)

    return resultado


def invocar_lambda_prueba(
    *,
    clave_s3: str,
    bucket: str | None = None,
    region: str | None = None,
) -> dict:
    """Invoca la Lambda con un evento S3 sintético (útil para probar sin re-subir ficheros)."""
    bucket = bucket or AWS_S3_BUCKET
    region = region or AWS_REGION

    evento = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": bucket},
                    "object": {"key": clave_s3},
                }
            }
        ]
    }

    lambda_client = _cliente_lambda(region)
    respuesta = lambda_client.invoke(
        FunctionName=LAMBDA_FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(evento).encode("utf-8"),
    )

    cuerpo = respuesta["Payload"].read().decode("utf-8")
    try:
        return json.loads(cuerpo)
    except json.JSONDecodeError:
        return {"respuesta_raw": cuerpo, "status_code": respuesta.get("StatusCode")}
