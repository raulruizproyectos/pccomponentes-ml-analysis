"""
CLI para operaciones AWS del proyecto (Fase 01).

Soporta memorias RAM y tarjetas gráficas con la misma estructura de pipeline.

Comandos:
    estado        Muestra qué ficheros locales existen por categoría.
    crear-bucket  Crea y configura el bucket S3 del proyecto.
    verificar-s3  Comprueba si el bucket existe y sus prefijos.
    subir         Sube JSON locales a S3 (brutos, procesados o ambos).
    etl           Ejecuta la carga a PostgreSQL desde datos procesados locales.
    pipeline      Ejecuta limpieza + carga a PostgreSQL.
    probar-db     Prueba conexión a PostgreSQL RDS.
    aplicar-esquema  Crea tablas en RDS desde database/esquema.sql.
    desplegar-lambda Crea/actualiza Lambda ETL + trigger S3.
    verificar-lambda Comprueba función Lambda y notificaciones S3.
    probar-lambda   Invoca Lambda con un evento S3 de prueba.
    setup         Ejecuta el flujo completo de montaje (tarde AWS).

Variables de entorno:
    AWS_S3_BUCKET, AWS_REGION, DATABASE_URL
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

Ejemplos:
    python ejecutar_aws.py estado
    python ejecutar_aws.py crear-bucket
    python ejecutar_aws.py verificar-s3
    python ejecutar_aws.py etl --categoria ram --dry-run
    python ejecutar_aws.py subir --categoria todas --tipo procesados --omitir-faltantes
    python ejecutar_aws.py pipeline --categoria ram
    python ejecutar_aws.py setup
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aws.categorias import obtener_categoria, resolver_categorias
from aws.orquestador import (
    ejecutar_etl_local,
    ejecutar_pipeline_local,
    resumen_disponibilidad_local,
)
from aws.infra_lambda import (
    desplegar_lambda,
    empaquetar_lambda,
    invocar_lambda_prueba,
    verificar_lambda,
)
from aws.infra_rds import aplicar_esquema, probar_conexion
from aws.infra_s3 import aprovisionar_bucket, verificar_bucket
from aws.s3_client import ClienteS3
from config.settings import AWS_REGION, AWS_S3_BUCKET, DATABASE_URL


def _crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Operaciones AWS: S3 y pipeline ETL (RAM + tarjetas gráficas)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    subparsers.add_parser("estado", help="Muestra disponibilidad local por categoría")

    crear_bucket = subparsers.add_parser(
        "crear-bucket",
        help="Crea y configura el bucket S3 (seguridad + prefijos)",
    )
    crear_bucket.add_argument("--bucket", default=None, help="Nombre del bucket S3")
    crear_bucket.add_argument("--region", default=None, help="Región AWS")
    crear_bucket.add_argument(
        "--forzar-prefijos",
        action="store_true",
        help="Recrea los marcadores de prefijos aunque el bucket ya exista",
    )

    verificar_s3 = subparsers.add_parser(
        "verificar-s3",
        help="Comprueba existencia del bucket y prefijos del pipeline",
    )
    verificar_s3.add_argument("--bucket", default=None, help="Nombre del bucket S3")
    verificar_s3.add_argument("--region", default=None, help="Región AWS")

    subir = subparsers.add_parser("subir", help="Sube JSON locales a S3")
    subir.add_argument(
        "--categoria",
        choices=["ram", "tarjetas_graficas", "todas"],
        default="todas",
        help="Categoría a subir",
    )
    subir.add_argument(
        "--tipo",
        choices=["brutos", "procesados", "todo"],
        default="todo",
        help="Qué conjunto de ficheros subir",
    )
    subir.add_argument(
        "--omitir-faltantes",
        action="store_true",
        default=True,
        help="No fallar si faltan ficheros de una categoría (default: activado)",
    )
    subir.add_argument(
        "--estricto",
        action="store_true",
        help="Falla si falta cualquier fichero requerido",
    )

    etl = subparsers.add_parser("etl", help="Carga datos procesados locales a PostgreSQL")
    etl.add_argument(
        "--categoria",
        choices=["ram", "tarjetas_graficas", "todas"],
        default="ram",
        help="Categoría a cargar",
    )
    etl.add_argument("--dry-run", action="store_true", help="Solo prepara tuplas, sin insertar")

    pipeline = subparsers.add_parser(
        "pipeline",
        help="Ejecuta limpieza local y luego carga a PostgreSQL",
    )
    pipeline.add_argument(
        "--categoria",
        choices=["ram", "tarjetas_graficas", "todas"],
        default="ram",
        help="Categoría a procesar",
    )
    pipeline.add_argument("--dry-run", action="store_true")

    subparsers.add_parser("probar-db", help="Prueba conexión a PostgreSQL RDS")

    aplicar = subparsers.add_parser(
        "aplicar-esquema",
        help="Aplica database/esquema.sql en RDS",
    )

    setup = subparsers.add_parser(
        "setup",
        help="Flujo completo: S3 + RDS + ETL + subida",
    )
    setup.add_argument(
        "--saltar-etl",
        action="store_true",
        help="No cargar datos si Raúl ya los insertó",
    )
    setup.add_argument(
        "--saltar-subida",
        action="store_true",
        help="No subir ficheros a S3",
    )

    empaquetar = subparsers.add_parser(
        "empaquetar-lambda",
        help="Genera el ZIP de despliegue Lambda (sin subir a AWS)",
    )
    empaquetar.add_argument(
        "--salida",
        default=None,
        help="Ruta del ZIP de salida (opcional)",
    )

    desplegar = subparsers.add_parser(
        "desplegar-lambda",
        help="Empaqueta, despliega Lambda y configura trigger S3",
    )
    desplegar.add_argument("--bucket", default=None, help="Bucket S3 del proyecto")
    desplegar.add_argument("--region", default=None, help="Región AWS")
    desplegar.add_argument(
        "--sin-empaquetar",
        action="store_true",
        help="Reutiliza build/lambda_package.zip sin regenerarlo",
    )

    verificar_lambda_cmd = subparsers.add_parser(
        "verificar-lambda",
        help="Comprueba función Lambda y notificaciones S3",
    )
    verificar_lambda_cmd.add_argument("--bucket", default=None, help="Bucket S3")
    verificar_lambda_cmd.add_argument("--region", default=None, help="Región AWS")

    probar_lambda = subparsers.add_parser(
        "probar-lambda",
        help="Invoca Lambda con un evento S3 sintético",
    )
    probar_lambda.add_argument(
        "--clave",
        required=True,
        help="Clave S3 del objeto, ej. procesados/tarjetas_graficas/productos_...json",
    )
    probar_lambda.add_argument("--bucket", default=None, help="Bucket S3")
    probar_lambda.add_argument("--region", default=None, help="Región AWS")

    return parser


def _database_url() -> str:
    database_url = DATABASE_URL or os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise ValueError("Falta DATABASE_URL en el entorno o en .env")
    return database_url


def _comando_estado() -> int:
    resumen = resumen_disponibilidad_local()
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    return 0


def _comando_crear_bucket(args: argparse.Namespace) -> int:
    resultado = aprovisionar_bucket(
        bucket=args.bucket or AWS_S3_BUCKET,
        region=args.region or AWS_REGION,
        forzar_prefijos=args.forzar_prefijos,
    )
    print(resultado.mensaje)
    print(f"Region: {resultado.region}")
    if resultado.prefijos:
        print("Prefijos creados:")
        for prefijo in resultado.prefijos:
            print(f"  - s3://{resultado.bucket}/{prefijo}")
    return 0


def _comando_verificar_s3(args: argparse.Namespace) -> int:
    resultado = verificar_bucket(
        bucket=args.bucket or AWS_S3_BUCKET,
        region=args.region or AWS_REGION,
    )
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    return 0


def _comando_subir(args: argparse.Namespace) -> int:
    cliente = ClienteS3()
    omitir_faltantes = not args.estricto

    resultados = cliente.subir_categorias(
        args.categoria,
        tipo=args.tipo,
        omitir_faltantes=omitir_faltantes,
    )

    for categoria, uris in resultados.items():
        print(f"Categoría {categoria}: {len(uris)} fichero(s) subido(s)")

    print("Subida a S3 completada.")
    return 0


def _comando_etl(args: argparse.Namespace) -> int:
    database_url = _database_url() if not args.dry_run else "dry-run://local"
    resultados = {}

    for categoria in resolver_categorias(args.categoria):
        try:
            resultados[categoria.nombre] = ejecutar_etl_local(
                categoria,
                database_url,
                dry_run=args.dry_run,
            )
        except FileNotFoundError as error:
            if args.categoria == "todas":
                print(f"Omitido [{categoria.nombre}]: {error}")
                continue
            raise

    print(f"Resultado ETL: {resultados}")
    return 0


def _comando_probar_db() -> int:
    resultado = probar_conexion(_database_url())
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    return 0


def _comando_aplicar_esquema() -> int:
    resultado = aplicar_esquema(_database_url())
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    return 0


def _paso(titulo: str) -> None:
    print(f"\n=== {titulo} ===")


def _comando_setup(args: argparse.Namespace) -> int:
    _paso("1/6 Datos locales")
    print(json.dumps(resumen_disponibilidad_local(), indent=2, ensure_ascii=False))

    _paso("2/6 Bucket S3")
    bucket = aprovisionar_bucket(
        bucket=AWS_S3_BUCKET,
        region=AWS_REGION,
        forzar_prefijos=True,
    )
    print(bucket.mensaje)
    s3 = verificar_bucket(AWS_S3_BUCKET, AWS_REGION)
    print(json.dumps(s3, indent=2, ensure_ascii=False))

    _paso("3/6 Conexión RDS")
    db = probar_conexion(_database_url())
    print(json.dumps(db, indent=2, ensure_ascii=False))

    tablas_requeridas = {
        "productos",
        "especificaciones_ram",
        "distribucion_valoraciones",
        "resenas",
        "especificaciones_gpu",
    }
    if not tablas_requeridas.issubset(set(db["tablas"])):
        _paso("4/6 Esquema SQL")
        esquema = aplicar_esquema(_database_url())
        print(json.dumps(esquema, indent=2, ensure_ascii=False))
    else:
        print("Las tablas ya existen. Esquema omitido.")

    if not args.saltar_etl:
        _paso("5/6 Carga ETL RAM")
        categoria = obtener_categoria("ram")
        etl = ejecutar_etl_local(categoria, _database_url(), dry_run=False)
        print(json.dumps(etl, indent=2, ensure_ascii=False))
    else:
        print("ETL omitido por --saltar-etl")

    if not args.saltar_subida:
        _paso("6/6 Subida S3")
        cliente = ClienteS3()
        subidos = cliente.subir_categorias(
            "ram",
            tipo="todo",
            omitir_faltantes=True,
        )
        print(json.dumps(subidos, indent=2, ensure_ascii=False))
    else:
        print("Subida S3 omitida por --saltar-subida")

    print("\nSetup completado.")
    return 0


def _comando_empaquetar_lambda(args: argparse.Namespace) -> int:
    destino = Path(args.salida) if args.salida else None
    paquete = empaquetar_lambda(destino=destino)
    print(f"Paquete Lambda generado: {paquete}")
    print(f"Tamaño: {paquete.stat().st_size / (1024 * 1024):.1f} MB")
    return 0


def _comando_desplegar_lambda(args: argparse.Namespace) -> int:
    resultado = desplegar_lambda(
        database_url=_database_url(),
        bucket=args.bucket or AWS_S3_BUCKET,
        region=args.region or AWS_REGION,
        empaquetar=not args.sin_empaquetar,
    )
    print(resultado.mensaje)
    print(json.dumps(resultado.__dict__, indent=2, ensure_ascii=False))
    print(
        "\nNota RDS: Lambda se conecta desde la red de AWS. "
        "Si el RDS es público, el security group debe permitir "
        "PostgreSQL (5432) desde 0.0.0.0/0 o usar Lambda en VPC."
    )
    return 0


def _comando_verificar_lambda(args: argparse.Namespace) -> int:
    resultado = verificar_lambda(
        bucket=args.bucket or AWS_S3_BUCKET,
        region=args.region or AWS_REGION,
    )
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    return 0


def _comando_probar_lambda(args: argparse.Namespace) -> int:
    resultado = invocar_lambda_prueba(
        clave_s3=args.clave,
        bucket=args.bucket or AWS_S3_BUCKET,
        region=args.region or AWS_REGION,
    )
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    return 0


def _comando_pipeline(args: argparse.Namespace) -> int:
    database_url = _database_url() if not args.dry_run else "dry-run://local"
    resultados = {}

    for categoria in resolver_categorias(args.categoria):
        resultados[categoria.nombre] = ejecutar_pipeline_local(
            categoria,
            database_url,
            dry_run=args.dry_run,
        )

    print(f"Resultado pipeline: {resultados}")
    return 0


def main() -> int:
    args = _crear_parser().parse_args()

    try:
        if args.comando == "estado":
            return _comando_estado()
        if args.comando == "crear-bucket":
            return _comando_crear_bucket(args)
        if args.comando == "verificar-s3":
            return _comando_verificar_s3(args)
        if args.comando == "subir":
            return _comando_subir(args)
        if args.comando == "etl":
            return _comando_etl(args)
        if args.comando == "pipeline":
            return _comando_pipeline(args)
        if args.comando == "probar-db":
            return _comando_probar_db()
        if args.comando == "aplicar-esquema":
            return _comando_aplicar_esquema()
        if args.comando == "setup":
            return _comando_setup(args)
        if args.comando == "empaquetar-lambda":
            return _comando_empaquetar_lambda(args)
        if args.comando == "desplegar-lambda":
            return _comando_desplegar_lambda(args)
        if args.comando == "verificar-lambda":
            return _comando_verificar_lambda(args)
        if args.comando == "probar-lambda":
            return _comando_probar_lambda(args)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())