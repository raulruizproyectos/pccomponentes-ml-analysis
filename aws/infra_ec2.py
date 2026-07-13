"""Despliegue sencillo de FastAPI en una instancia EC2."""

from __future__ import annotations

import json
import time

import boto3
from botocore.exceptions import ClientError

from config.settings import AWS_REGION, AWS_S3_BUCKET


NOMBRE_INSTANCIA = "pccomponentes-fastapi"
NOMBRE_ROL = "pccomponentes-ec2-fastapi-role"
NOMBRE_PERFIL = "pccomponentes-ec2-fastapi-profile"
NOMBRE_SG = "pccomponentes-fastapi-sg"
NOMBRE_IP = "pccomponentes-fastapi-ip"
PARAMETRO_DATABASE_URL = "/pccomponentes/fastapi/database-url"
REPOSITORIO = "https://github.com/raulruizproyectos/pccomponentes-ml-analysis.git"


def _cliente(servicio, region=None):
    return boto3.client(servicio, region_name=region or AWS_REGION)


def _codigo_error(error):
    return error.response.get("Error", {}).get("Code", "")


def _obtener_red_rds(region):
    rds = _cliente("rds", region)
    respuesta = rds.describe_db_instances(DBInstanceIdentifier="database-1")
    instancia = respuesta["DBInstances"][0]

    return {
        "vpc_id": instancia["DBSubnetGroup"]["VpcId"],
        "subnet_ids": [
            subnet["SubnetIdentifier"]
            for subnet in instancia["DBSubnetGroup"]["Subnets"]
        ],
        "security_group_ids": [
            grupo["VpcSecurityGroupId"]
            for grupo in instancia["VpcSecurityGroups"]
        ],
    }


def _guardar_database_url(database_url, region):
    _cliente("ssm", region).put_parameter(
        Name=PARAMETRO_DATABASE_URL,
        Description="Conexion PostgreSQL usada por FastAPI en EC2",
        Value=database_url,
        Type="SecureString",
        Overwrite=True,
    )


def _asegurar_rol(region):
    iam = _cliente("iam", region)
    creado = False
    confianza = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    try:
        iam.get_role(RoleName=NOMBRE_ROL)
    except ClientError as error:
        if _codigo_error(error) != "NoSuchEntity":
            raise
        iam.create_role(
            RoleName=NOMBRE_ROL,
            AssumeRolePolicyDocument=json.dumps(confianza),
            Description="Rol de la API FastAPI en EC2",
        )
        creado = True

    cuenta = _cliente("sts", region).get_caller_identity()["Account"]
    permiso_parametro = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "ssm:GetParameter",
                "Resource": (
                    f"arn:aws:ssm:{region}:{cuenta}:parameter"
                    f"{PARAMETRO_DATABASE_URL}"
                ),
            }
        ],
    }
    iam.put_role_policy(
        RoleName=NOMBRE_ROL,
        PolicyName="leer-database-url",
        PolicyDocument=json.dumps(permiso_parametro),
    )
    if AWS_S3_BUCKET:
        permiso_s3 = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "s3:PutObject",
                    "Resource": f"arn:aws:s3:::{AWS_S3_BUCKET}/brutos/ram/*",
                }
            ],
        }
        iam.put_role_policy(
            RoleName=NOMBRE_ROL,
            PolicyName="subir-scraping-s3",
            PolicyDocument=json.dumps(permiso_s3),
        )
    iam.attach_role_policy(
        RoleName=NOMBRE_ROL,
        PolicyArn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    )

    try:
        perfil = iam.get_instance_profile(
            InstanceProfileName=NOMBRE_PERFIL
        )["InstanceProfile"]
    except ClientError as error:
        if _codigo_error(error) != "NoSuchEntity":
            raise
        perfil = iam.create_instance_profile(
            InstanceProfileName=NOMBRE_PERFIL
        )["InstanceProfile"]
        creado = True

    roles = [rol["RoleName"] for rol in perfil.get("Roles", [])]
    if NOMBRE_ROL not in roles:
        iam.add_role_to_instance_profile(
            InstanceProfileName=NOMBRE_PERFIL,
            RoleName=NOMBRE_ROL,
        )
        creado = True

    if creado:
        time.sleep(10)


def _asegurar_security_group(red, region):
    ec2 = _cliente("ec2", region)
    respuesta = ec2.describe_security_groups(
        Filters=[
            {"Name": "group-name", "Values": [NOMBRE_SG]},
            {"Name": "vpc-id", "Values": [red["vpc_id"]]},
        ]
    )

    if respuesta["SecurityGroups"]:
        security_group_id = respuesta["SecurityGroups"][0]["GroupId"]
    else:
        security_group_id = ec2.create_security_group(
            GroupName=NOMBRE_SG,
            Description="Acceso publico a FastAPI",
            VpcId=red["vpc_id"],
        )["GroupId"]
        ec2.create_tags(
            Resources=[security_group_id],
            Tags=[{"Key": "Project", "Value": "pccomponentes"}],
        )

    try:
        ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": 8000,
                    "ToPort": 8000,
                    "IpRanges": [
                        {
                            "CidrIp": "0.0.0.0/0",
                            "Description": "API publica para la evaluacion",
                        }
                    ],
                }
            ],
        )
    except ClientError as error:
        if _codigo_error(error) != "InvalidPermission.Duplicate":
            raise

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
                                "Description": "FastAPI en EC2",
                            }
                        ],
                    }
                ],
            )
        except ClientError as error:
            if _codigo_error(error) != "InvalidPermission.Duplicate":
                raise

    return security_group_id


def _crear_user_data(region):
    return f"""#!/bin/bash
set -euo pipefail

dnf install -y git python3.11
cd /opt
git clone {REPOSITORIO} pccomponentes-ml-analysis
cd pccomponentes-ml-analysis

python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-api.txt

mkdir -p /etc/pccomponentes
DATABASE_URL=$(aws ssm get-parameter --region {region} --name {PARAMETRO_DATABASE_URL} --with-decryption --query Parameter.Value --output text)
printf 'DATABASE_URL=%s\\n' "$DATABASE_URL" > /etc/pccomponentes/api.env
chmod 600 /etc/pccomponentes/api.env

chmod +x deploy/iniciar_fastapi_tmux.sh
deploy/iniciar_fastapi_tmux.sh
"""


def _buscar_instancia(ec2):
    respuesta = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [NOMBRE_INSTANCIA]},
            {
                "Name": "instance-state-name",
                "Values": ["pending", "running", "stopping", "stopped"],
            },
        ]
    )
    for reserva in respuesta["Reservations"]:
        for instancia in reserva["Instances"]:
            return instancia
    return None


def _asegurar_ip_elastica(instance_id, region):
    ec2 = _cliente("ec2", region)
    respuesta = ec2.describe_addresses(
        Filters=[{"Name": "tag:Name", "Values": [NOMBRE_IP]}]
    )

    if respuesta["Addresses"]:
        direccion = respuesta["Addresses"][0]
    else:
        direccion = ec2.allocate_address(
            Domain="vpc",
            NetworkBorderGroup=region,
            TagSpecifications=[
                {
                    "ResourceType": "elastic-ip",
                    "Tags": [
                        {"Key": "Name", "Value": NOMBRE_IP},
                        {"Key": "Project", "Value": "pccomponentes"},
                    ],
                }
            ],
        )

    if direccion.get("InstanceId") != instance_id:
        ec2.associate_address(
            InstanceId=instance_id,
            AllocationId=direccion["AllocationId"],
        )

    return direccion["PublicIp"]


def desplegar_ec2(database_url, region=None):
    region = region or AWS_REGION
    ec2 = _cliente("ec2", region)
    existente = _buscar_instancia(ec2)
    _asegurar_rol(region)

    if existente:
        if existente["State"]["Name"] == "stopped":
            ec2.start_instances(InstanceIds=[existente["InstanceId"]])
            ec2.get_waiter("instance_running").wait(
                InstanceIds=[existente["InstanceId"]]
            )
        _asegurar_ip_elastica(existente["InstanceId"], region)
        return verificar_ec2(region)

    red = _obtener_red_rds(region)
    _guardar_database_url(database_url, region)
    security_group_id = _asegurar_security_group(red, region)

    ami = _cliente("ssm", region).get_parameter(
        Name="/aws/service/ami-amazon-linux-latest/"
        "al2023-ami-kernel-default-x86_64"
    )["Parameter"]["Value"]

    respuesta = ec2.run_instances(
        ImageId=ami,
        InstanceType="t3.micro",
        MinCount=1,
        MaxCount=1,
        IamInstanceProfile={"Name": NOMBRE_PERFIL},
        UserData=_crear_user_data(region),
        NetworkInterfaces=[
            {
                "DeviceIndex": 0,
                "SubnetId": red["subnet_ids"][0],
                "Groups": [security_group_id],
                "AssociatePublicIpAddress": True,
            }
        ],
        MetadataOptions={
            "HttpTokens": "required",
            "HttpEndpoint": "enabled",
        },
        BlockDeviceMappings=[
            {
                "DeviceName": "/dev/xvda",
                "Ebs": {
                    "VolumeSize": 12,
                    "VolumeType": "gp3",
                    "Encrypted": True,
                    "DeleteOnTermination": True,
                },
            }
        ],
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": NOMBRE_INSTANCIA},
                    {"Key": "Project", "Value": "pccomponentes"},
                ],
            }
        ],
    )
    instance_id = respuesta["Instances"][0]["InstanceId"]
    ec2.get_waiter("instance_running").wait(InstanceIds=[instance_id])
    _asegurar_ip_elastica(instance_id, region)
    return verificar_ec2(region)


def verificar_ec2(region=None):
    region = region or AWS_REGION
    ec2 = _cliente("ec2", region)
    instancia = _buscar_instancia(ec2)

    if not instancia:
        return {"existe": False, "region": region}

    public_ip = instancia.get("PublicIpAddress")
    return {
        "existe": True,
        "region": region,
        "instance_id": instancia["InstanceId"],
        "estado": instancia["State"]["Name"],
        "tipo": instancia["InstanceType"],
        "public_ip": public_ip,
        "url": f"http://{public_ip}:8000" if public_ip else None,
    }
