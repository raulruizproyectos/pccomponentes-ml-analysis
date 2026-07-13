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
import time
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
LAMBDA_SECURITY_GROUP_NAME = "pccomponentes-lambda-sg"
LAMBDA_VPC_POLICY_ARN = (
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
)

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


def _cliente_ec2(region: str | None = None):
    return boto3.client("ec2", region_name=region or AWS_REGION)


def _codigo_error(error: ClientError) -> str:
    return error.response.get("Error", {}).get("Code", "")


def _nombre_rol(rol_arn: str) -> str:
    return rol_arn.rsplit("/", 1)[-1]


def _es_regla_publica_postgres(regla: dict) -> bool:
    return (
        not regla.get("IsEgress")
        and regla.get("IpProtocol") == "tcp"
        and regla.get("FromPort") == 5432
        and regla.get("ToPort") == 5432
        and regla.get("CidrIpv4") == "0.0.0.0/0"
    )


def _asegurar_permiso_vpc(nombre_rol: str, region: str) -> None:
    iam = _cliente_iam(region)
    permisos = iam.list_attached_role_policies(RoleName=nombre_rol)[
        "AttachedPolicies"
    ]
    if LAMBDA_VPC_POLICY_ARN not in [permiso["PolicyArn"] for permiso in permisos]:
        iam.attach_role_policy(
            RoleName=nombre_rol,
            PolicyArn=LAMBDA_VPC_POLICY_ARN,
        )
        time.sleep(10)


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
        rol_arn = _cliente_lambda(region).get_function_configuration(
            FunctionName=LAMBDA_FUNCTION_NAME
        )["Role"]
        nombre_rol = _nombre_rol(rol_arn)
    except ClientError as error:
        if _codigo_error(error) != "ResourceNotFoundException":
            raise
        try:
            respuesta = iam.get_role(RoleName=LAMBDA_ROLE_NAME)
            rol_arn = respuesta["Role"]["Arn"]
        except ClientError as role_error:
            if _codigo_error(role_error) != "NoSuchEntity":
                raise
            respuesta = iam.create_role(
                RoleName=LAMBDA_ROLE_NAME,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Rol para Lambda ETL pccomponentes-ml-analysis",
            )
            rol_arn = respuesta["Role"]["Arn"]
            time.sleep(10)
        nombre_rol = LAMBDA_ROLE_NAME

    iam.put_role_policy(
        RoleName=nombre_rol,
        PolicyName="pccomponentes-ml-lambda-inline",
        PolicyDocument=json.dumps(_politica_rol_lambda(bucket)),
    )
    _asegurar_permiso_vpc(nombre_rol, region or AWS_REGION)

    return rol_arn


def _asegurar_red_lambda(region: str) -> dict:
    """Conecta Lambda a la VPC de RDS y permite leer S3 sin Internet."""
    from aws.infra_ec2 import _obtener_red_rds

    red = _obtener_red_rds(region)
    ec2 = _cliente_ec2(region)
    grupos = ec2.describe_security_groups(
        Filters=[
            {"Name": "group-name", "Values": [LAMBDA_SECURITY_GROUP_NAME]},
            {"Name": "vpc-id", "Values": [red["vpc_id"]]},
        ]
    )["SecurityGroups"]

    if grupos:
        security_group_id = grupos[0]["GroupId"]
    else:
        security_group_id = ec2.create_security_group(
            GroupName=LAMBDA_SECURITY_GROUP_NAME,
            Description="Acceso de Lambda ETL a RDS",
            VpcId=red["vpc_id"],
        )["GroupId"]
        ec2.create_tags(
            Resources=[security_group_id],
            Tags=[{"Key": "Project", "Value": "pccomponentes"}],
        )

    for rds_security_group_id in red["security_group_ids"]:
        try:
            ec2.authorize_security_group_ingress(
                GroupId=rds_security_group_id,
                IpPermissions=[
                    {
                        "IpProtocol": "tcp",
                        "FromPort": 5432,
                        "ToPort": 5432,
                        "UserIdGroupPairs": [
                            {
                                "GroupId": security_group_id,
                                "Description": "Lambda ETL",
                            }
                        ],
                    }
                ],
            )
        except ClientError as error:
            if _codigo_error(error) != "InvalidPermission.Duplicate":
                raise

    tablas = ec2.describe_route_tables(
        Filters=[{"Name": "vpc-id", "Values": [red["vpc_id"]]}]
    )["RouteTables"]
    route_table_ids = []
    for tabla in tablas:
        asociaciones = tabla.get("Associations", [])
        usa_subred = any(
            asociacion.get("SubnetId") in red["subnet_ids"]
            for asociacion in asociaciones
        )
        es_principal = any(
            asociacion.get("Main") is True for asociacion in asociaciones
        )
        if usa_subred or es_principal:
            route_table_ids.append(tabla["RouteTableId"])

    servicio_s3 = f"com.amazonaws.{region}.s3"
    endpoints = ec2.describe_vpc_endpoints(
        Filters=[
            {"Name": "vpc-id", "Values": [red["vpc_id"]]},
            {"Name": "service-name", "Values": [servicio_s3]},
            {"Name": "vpc-endpoint-state", "Values": ["pending", "available"]},
        ]
    )["VpcEndpoints"]

    if endpoints:
        endpoint = endpoints[0]
        faltantes = list(
            set(route_table_ids) - set(endpoint.get("RouteTableIds", []))
        )
        if faltantes:
            ec2.modify_vpc_endpoint(
                VpcEndpointId=endpoint["VpcEndpointId"],
                AddRouteTableIds=faltantes,
            )
        endpoint_id = endpoint["VpcEndpointId"]
    else:
        endpoint_id = ec2.create_vpc_endpoint(
            VpcId=red["vpc_id"],
            ServiceName=servicio_s3,
            VpcEndpointType="Gateway",
            RouteTableIds=route_table_ids,
            TagSpecifications=[
                {
                    "ResourceType": "vpc-endpoint",
                    "Tags": [
                        {"Key": "Name", "Value": "pccomponentes-s3-endpoint"},
                        {"Key": "Project", "Value": "pccomponentes"},
                    ],
                }
            ],
        )["VpcEndpoint"]["VpcEndpointId"]

    return {
        "vpc_id": red["vpc_id"],
        "subnet_ids": red["subnet_ids"],
        "security_group_ids": [security_group_id],
        "rds_security_group_ids": red["security_group_ids"],
        "s3_endpoint_id": endpoint_id,
    }


def _cerrar_acceso_publico_rds(red: dict, region: str) -> None:
    ec2 = _cliente_ec2(region)
    for group_id in red["rds_security_group_ids"]:
        reglas = ec2.describe_security_group_rules(
            Filters=[{"Name": "group-id", "Values": [group_id]}]
        )["SecurityGroupRules"]
        reglas_publicas = [
            regla["SecurityGroupRuleId"]
            for regla in reglas
            if _es_regla_publica_postgres(regla)
        ]
        if reglas_publicas:
            ec2.revoke_security_group_ingress(
                GroupId=group_id,
                SecurityGroupRuleIds=reglas_publicas,
            )


def configurar_red_lambda(region: str | None = None) -> dict:
    """Aplica la red privada a la Lambda ya desplegada."""
    region = region or AWS_REGION
    lambda_client = _cliente_lambda(region)
    config = lambda_client.get_function_configuration(
        FunctionName=LAMBDA_FUNCTION_NAME
    )
    nombre_rol = _nombre_rol(config["Role"])
    _asegurar_permiso_vpc(nombre_rol, region)
    red = _asegurar_red_lambda(region)
    vpc_actual = config.get("VpcConfig", {})
    red_ya_configurada = (
        set(vpc_actual.get("SubnetIds", [])) == set(red["subnet_ids"])
        and set(vpc_actual.get("SecurityGroupIds", []))
        == set(red["security_group_ids"])
    )
    if not red_ya_configurada:
        lambda_client.update_function_configuration(
            FunctionName=LAMBDA_FUNCTION_NAME,
            VpcConfig={
                "SubnetIds": red["subnet_ids"],
                "SecurityGroupIds": red["security_group_ids"],
            },
        )
        lambda_client.get_waiter("function_updated_v2").wait(
            FunctionName=LAMBDA_FUNCTION_NAME
        )
    _cerrar_acceso_publico_rds(red, region)
    return red


def _asegurar_funcion_lambda(
    *,
    rol_arn: str,
    paquete: Path,
    database_url: str,
    bucket: str,
    red: dict,
    region: str | None = None,
) -> str:
    lambda_client = _cliente_lambda(region)
    region = region or AWS_REGION
    codigo_zip = paquete.read_bytes()

    variables = {
        "DATABASE_URL": database_url,
        "AWS_S3_BUCKET": bucket,
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
        lambda_client.get_waiter("function_updated_v2").wait(
            FunctionName=LAMBDA_FUNCTION_NAME
        )
        lambda_client.update_function_configuration(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Role=rol_arn,
            Handler=LAMBDA_HANDLER,
            Runtime=LAMBDA_RUNTIME,
            Timeout=LAMBDA_TIMEOUT,
            MemorySize=LAMBDA_MEMORY,
            Environment={"Variables": variables},
            VpcConfig={
                "SubnetIds": red["subnet_ids"],
                "SecurityGroupIds": red["security_group_ids"],
            },
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
            VpcConfig={
                "SubnetIds": red["subnet_ids"],
                "SecurityGroupIds": red["security_group_ids"],
            },
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
    """Crea una regla por categoría usando el último fichero bruto."""
    from aws.categorias import listar_categorias

    reglas = []

    for categoria in listar_categorias():
        prefijo = f"brutos/{categoria.slug}/"
        tipo_final = "detalle" if categoria.lista else "dataset"
        archivo_final = categoria.brutos[tipo_final].name
        reglas.append(
            {
                "Id": f"etl-brutos-{categoria.slug}",
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
    red = _asegurar_red_lambda(region)
    funcion_arn = _asegurar_funcion_lambda(
        rol_arn=rol_arn,
        paquete=paquete,
        database_url=database_url,
        bucket=bucket,
        red=red,
        region=region,
    )
    _cerrar_acceso_publico_rds(red, region)
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
                "vpc_id": config.get("VpcConfig", {}).get("VpcId"),
                "subnet_ids": config.get("VpcConfig", {}).get("SubnetIds", []),
                "security_group_ids": config.get("VpcConfig", {}).get(
                    "SecurityGroupIds", []
                ),
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
                            if filtro.get("Name", "").lower() == "prefix"
                        ),
                        None,
                    ),
                    "sufijo": next(
                        (
                            filtro["Value"]
                            for filtro in regla.get("Filter", {})
                            .get("Key", {})
                            .get("FilterRules", [])
                            if filtro.get("Name", "").lower() == "suffix"
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
