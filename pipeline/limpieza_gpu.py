# Limpieza de datos de tarjetas graficas.
# Lee el JSON de GPU ya preprocesado por IA y lo adapta al esquema comun del proyecto.
# Genera productos, especificaciones y distribucion de valoraciones para PostgreSQL.
# Las resenas GPU se dejan fuera por ahora porque no incluyen valoracion individual.

import json
from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]

RUTA_DATOS = (
    RAIZ_PROYECTO
    / "data"
    / "brutos"
    / "tarjetas_graficas"
    / "tarjetas_graficas.json"
)
RUTA_SALIDA = RAIZ_PROYECTO / "data" / "procesados" / "tarjetas_graficas"


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_json(datos, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=4)


def producto_id_gpu(producto):
    return f"gpu_{int(producto['id_producto']):04d}"


def limpiar_producto(producto, posicion):
    producto_id = producto_id_gpu(producto)

    return {
        "producto_id": producto_id,
        "nombre": producto.get("modelo"),
        "url": producto.get("url"),
        "sku": producto_id,
        "marca": producto.get("marca"),
        "categoria": "tarjeta_grafica",
        "precio": producto.get("precio_fijo") or producto.get("precio"),
        "moneda": "EUR",
        "valoracion_media": producto.get("valoracion_media") or producto.get("valoracion"),
        "total_opiniones": int(producto.get("numero_total_opiniones") or 0),
        "total_resenas_con_texto": len(producto.get("texto_resena") or []),
        "porcentaje_recomendacion": producto.get("porcentaje_recomendacion"),
        "numero_recomendaciones": int(producto.get("numero_recomendaciones") or 0),
        "pagina_origen": 1 + ((posicion - 1) // 24),
        "posicion_listado": posicion,
        "presente_en_detalle": True,
        "fuente": "pccomponentes_gpu_ia",
    }


def limpiar_especificaciones(producto):
    return {
        "producto_id": producto_id_gpu(producto),
        "gpu": producto.get("gpu"),
        "memoria_vram": producto.get("info_descriptiva.Memoria VRAM")
        or producto.get("memoria_vram"),
        "tipo_memoria": producto.get("tipo_memoria"),
        "bus_memoria": producto.get("bus_memoria"),
        "ancho_banda_memoria": producto.get("info_descriptiva.Ancho de banda memoria")
        or producto.get("info_descriptiva.Ancho de banda de memoria"),
        "velocidad_memoria": producto.get("velocidad_memoria"),
        "reloj_base": producto.get("reloj_base"),
        "reloj_boost": producto.get("reloj_boost"),
        "salidas_video": producto.get("salidas_video"),
        "resolucion_maxima": producto.get("resolucion_maxima"),
    }


def limpiar_distribucion_valoraciones(producto):
    return {
        "producto_id": producto_id_gpu(producto),
        "estrellas_5": int(producto.get("estrellas_5") or 0),
        "estrellas_4": int(producto.get("estrellas_4") or 0),
        "estrellas_3": int(producto.get("estrellas_3") or 0),
        "estrellas_2": int(producto.get("estrellas_2") or 0),
        "estrellas_1": int(producto.get("estrellas_1") or 0),
        "fuente_desglose": producto.get("fuente_desglose") or "gpu_ia",
    }


def preparar_datos_limpios():
    productos_originales = leer_json(RUTA_DATOS)

    productos = []
    especificaciones = []
    distribuciones = []

    for posicion, producto in enumerate(productos_originales, start=1):
        productos.append(limpiar_producto(producto, posicion))
        especificaciones.append(limpiar_especificaciones(producto))
        distribuciones.append(limpiar_distribucion_valoraciones(producto))

    return {
        "productos": productos,
        "especificaciones": especificaciones,
        "distribuciones": distribuciones,
        "resenas": [],
    }


def validar_resultados(datos_limpios):
    assert len(datos_limpios["productos"]) == 500
    assert len(datos_limpios["especificaciones"]) == 500
    assert len(datos_limpios["distribuciones"]) == 500

    ids = [producto["producto_id"] for producto in datos_limpios["productos"]]
    urls = [producto["url"] for producto in datos_limpios["productos"]]

    assert len(ids) == len(set(ids))
    assert len(urls) == len(set(urls))
    assert all(producto["nombre"] for producto in datos_limpios["productos"])
    assert all(producto["precio"] is not None for producto in datos_limpios["productos"])


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
