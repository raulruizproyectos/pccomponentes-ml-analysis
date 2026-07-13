"""Comprobación sencilla de los disparadores S3 de Lambda."""

from aws.infra_lambda import _crear_reglas_notificacion_s3


def main() -> None:
    reglas = _crear_reglas_notificacion_s3("arn:lambda:prueba")

    assert len(reglas) == 2

    filtros = {}
    for regla in reglas:
        valores = regla["Filter"]["Key"]["FilterRules"]
        filtros[valores[0]["Value"]] = valores[1]["Value"]

    assert filtros == {
        "procesados/ram/": "resenas_ram_limpias.json",
        "procesados/tarjetas_graficas/": (
            "resenas_tarjetas_graficas_limpias.json"
        ),
    }

    print("Lambda: comprobación correcta")


if __name__ == "__main__":
    main()
