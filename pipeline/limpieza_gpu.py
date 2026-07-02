# Limpieza de datos de tarjetas gráficas.
# Misma interfaz que limpieza_ram.py para integrarse con el orquestador AWS.
# Pendiente: implementar cuando exista el scraper de listado + detalle GPU.


import json
from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]

RUTA_LISTADO = RAIZ_PROYECTO / "data" / "brutos" / "tarjetas_graficas" / "listado_tarjetas_graficas.json"
RUTA_DETALLE = RAIZ_PROYECTO / "data" / "brutos" / "tarjetas_graficas" / "detalle_tarjetas_graficas.json"
RUTA_SALIDA = RAIZ_PROYECTO / "data" / "procesados" / "tarjetas_graficas"


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_json(datos, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False)


def preparar_datos_limpios():
    if not RUTA_LISTADO.is_file() or not RUTA_DETALLE.is_file():
        raise FileNotFoundError(
            "Faltan los JSON brutos de tarjetas gráficas. "
            "Ejecuta primero el scraper de listado + detalle GPU."
        )

    raise NotImplementedError(
        "La limpieza de tarjetas gráficas está pendiente. "
        "Replica la lógica de limpieza_ram.py cuando existan los datos brutos."
    )


def validar_resultados(datos_limpios):
    assert datos_limpios["productos"]
    assert datos_limpios["especificaciones"]


def main():
    datos_limpios = preparar_datos_limpios()
    validar_resultados(datos_limpios)

    guardar_json(
        datos_limpios["productos"],
        RUTA_SALIDA / "productos_tarjetas_graficas_limpios.json",
    )
    guardar_json(
        datos_limpios["especificaciones"],
        RUTA_SALIDA / "especificaciones_tarjetas_graficas_limpias.json",
    )
    guardar_json(
        datos_limpios["distribuciones"],
        RUTA_SALIDA / "distribucion_valoraciones_tarjetas_graficas_limpia.json",
    )
    guardar_json(
        datos_limpios["resenas"],
        RUTA_SALIDA / "resenas_tarjetas_graficas_limpias.json",
    )

    print("Limpieza GPU completada")
    print(f"Productos: {len(datos_limpios['productos'])}")
    print(f"Especificaciones: {len(datos_limpios['especificaciones'])}")
    print(f"Distribuciones: {len(datos_limpios['distribuciones'])}")
    print(f"Resenas: {len(datos_limpios['resenas'])}")


if __name__ == "__main__":
    main()