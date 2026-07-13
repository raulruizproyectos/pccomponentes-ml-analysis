"""Comprobación sencilla de los disparadores S3 de Lambda."""

from aws.infra_lambda import (
    _crear_reglas_notificacion_s3,
    _es_regla_publica_postgres,
    _nombre_rol,
)


def main() -> None:
    reglas = _crear_reglas_notificacion_s3("arn:lambda:prueba")

    assert len(reglas) == 2

    filtros = {}
    for regla in reglas:
        valores = regla["Filter"]["Key"]["FilterRules"]
        filtros[valores[0]["Value"]] = valores[1]["Value"]

    assert filtros == {
        "brutos/ram/": "detalle_ram.json",
        "brutos/tarjetas_graficas/": "tarjetas_graficas.json",
    }
    assert _nombre_rol(
        "arn:aws:iam::094660904351:role/service-role/rol-lambda"
    ) == "rol-lambda"
    regla = {
        "IsEgress": False,
        "IpProtocol": "tcp",
        "FromPort": 5432,
        "ToPort": 5432,
        "CidrIpv4": "0.0.0.0/0",
    }
    assert _es_regla_publica_postgres(regla)
    regla["CidrIpv4"] = "93.176.134.17/32"
    assert not _es_regla_publica_postgres(regla)

    print("Lambda: comprobación correcta")


if __name__ == "__main__":
    main()
