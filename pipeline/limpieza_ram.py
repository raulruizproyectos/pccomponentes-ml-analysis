# Limpieza de datos de memorias RAM.
# Este script lee los JSON brutos del scraping, organiza los datos principales
# y genera archivos JSON limpios para productos, especificaciones, valoraciones y resenas.
# La idea es dejar los datos preparados antes de cargarlos en PostgreSQL.


import json
from pathlib import Path
import re


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]

RUTA_LISTADO = RAIZ_PROYECTO / "data" / "brutos" / "ram" / "listado_ram.json"
RUTA_DETALLE = RAIZ_PROYECTO / "data" / "brutos" / "ram" / "detalle_ram.json"

RUTA_SALIDA = RAIZ_PROYECTO / "data" / "procesados" / "ram"

MARCAS_RAM = [
    "Forgeon",
    "Corsair",
    "Kingston",
    "Crucial",
    "G.Skill",
    "Team Group",
    "Patriot",
    "PNY",
    "ADATA",
    "Samsung",
    "Lexar",
    "Kioxia",
    "Silicon Power",
    "Acer",
    "Synology",
    "GoodRam",
    "Mushkin",
    "Apacer",
    "Biwin",
    "AFOX",
    "Innovation IT",
    "Intel",
    "Dell",
    "HPE",
    "Lenovo",
    "HP",
    "QNAP",
    "2-Power",
    "Fujitsu",
    "Hikvision",
    "Biostar",
    "CoreParts",
]


def corregir_codificacion(valor):
    if isinstance(valor, str):
        texto = valor

        for _ in range(3):
            partes_corregidas = []

            for parte in re.split(r"([ \t\r\n]+)", texto):
                try:
                    parte = parte.encode("latin1").decode("utf-8")
                except UnicodeError:
                    pass

                partes_corregidas.append(parte)

            texto_corregido = "".join(partes_corregidas)

            if texto_corregido == texto:
                break

            texto = texto_corregido

        return texto

    if isinstance(valor, list):
        return [
            corregir_codificacion(elemento)
            for elemento in valor
        ]

    if isinstance(valor, dict):
        return {
            clave: corregir_codificacion(elemento)
            for clave, elemento in valor.items()
        }

    return valor


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        datos = json.load(archivo)

    return corregir_codificacion(datos)


def guardar_json(datos, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False)


def detectar_marca(nombre):
    nombre = (nombre or "").lower()

    for marca in MARCAS_RAM:
        if marca.lower() in nombre:
            return marca

    return None


def extraer_frecuencia_mhz(nombre):
    partes = (nombre or "").replace("/", " ").split()

    for parte in partes:
        parte_limpia = parte.lower().replace("mhz", "").replace("mt", "")

        if parte_limpia.isdigit():
            numero = int(parte_limpia)

            if 800 <= numero <= 9000:
                return numero

    return None


def capacidad_es_valida(valor):
    capacidades_validas = {
        0.25, 0.5, 1, 2, 4, 8, 12, 16, 24, 32,
        48, 64, 96, 128, 192, 256, 384, 512,
        768, 1024, 1536, 2048, 3072, 4096,
    }

    return (
        isinstance(valor, (int, float))
        and valor in capacidades_validas
    )


def extraer_capacidad_gb(nombre):
    partes = (nombre or "").lower().replace("/", " ").split()

    for indice, parte in enumerate(partes):
        parte_limpia = parte.strip("(),")

        if parte_limpia.endswith("gb"):
            cantidad = parte_limpia[:-2].replace(",", ".")

            componentes = cantidad.split("x")

            if (
                len(componentes) == 2
                and componentes[0].isdigit()
                and componentes[1].isdigit()
            ):
                capacidad = (
                    int(componentes[0])
                    * int(componentes[1])
                )

                if capacidad_es_valida(capacidad):
                    return capacidad

            try:
                capacidad = float(cantidad)
            except ValueError:
                capacidad = None

            if capacidad_es_valida(capacidad):
                return capacidad

        if parte_limpia == "gb" and indice > 0:
            cantidad = partes[indice - 1].replace(",", ".")

            try:
                capacidad = float(cantidad)
            except ValueError:
                capacidad = None

            if capacidad_es_valida(capacidad):
                return capacidad

    return None


def limpiar_producto(producto_listado, producto_detalle):
    opiniones = producto_detalle.get("opiniones") if producto_detalle else {}
    nombre = producto_detalle.get("nombre") if producto_detalle else producto_listado.get("nombre")

    producto_limpio = {
        "producto_id": producto_listado.get("id"),
        "nombre": nombre,
        "url": producto_detalle.get("url") if producto_detalle else producto_listado.get("url"),
        "sku": producto_detalle.get("sku") if producto_detalle else producto_listado.get("sku"),
        "marca": detectar_marca(nombre),
        "categoria": "memoria_ram",
        "precio": producto_detalle.get("precio") if producto_detalle else producto_listado.get("precio_listado"),
        "moneda": producto_detalle.get("moneda") if producto_detalle else "EUR",
        "valoracion_media": opiniones.get("valoracion_media") or producto_listado.get("valoracion_listado"),
        "total_opiniones": opiniones.get("total_opiniones") or producto_listado.get("num_opiniones_listado"),
        "total_resenas_con_texto": opiniones.get("total_resenas_con_texto"),
        "porcentaje_recomendacion": opiniones.get("porcentaje_recomendacion"),
        "numero_recomendaciones": opiniones.get("recomendaciones"),
        "pagina_origen": producto_listado.get("pagina_origen"),
        "posicion_listado": producto_listado.get("posicion_listado"),
        "presente_en_detalle": producto_detalle is not None,
        "fuente": "pccomponentes_ram",
    }

    return producto_limpio


def limpiar_especificaciones(producto_detalle):
    especificaciones = producto_detalle.get("especificaciones") or {}
    nombre = producto_detalle.get("nombre")

    frecuencia_mhz = (
        especificaciones.get("frecuencia_mhz")
        or extraer_frecuencia_mhz(nombre)
    )

    capacidad_gb = extraer_capacidad_gb(nombre)
    num_modulos = especificaciones.get("num_modulos")
    capacidad_por_modulo_gb = especificaciones.get(
        "capacidad_por_modulo_gb"
    )

    if capacidad_gb is None:
        capacidad_original = especificaciones.get("capacidad_gb")

        if capacidad_es_valida(capacidad_original):
            capacidad_gb = capacidad_original

    if capacidad_gb is not None and num_modulos:
        capacidad_calculada = capacidad_gb / num_modulos

        if capacidad_es_valida(capacidad_calculada):
            capacidad_por_modulo_gb = capacidad_calculada
    elif not capacidad_es_valida(capacidad_por_modulo_gb):
        capacidad_por_modulo_gb = None

    especificaciones_limpias = {
        "producto_id": producto_detalle.get("id"),
        "tipo_memoria": especificaciones.get("tipo_memoria"),
        "capacidad_gb": capacidad_gb,
        "kit": especificaciones.get("kit"),
        "num_modulos": num_modulos,
        "capacidad_por_modulo_gb": capacidad_por_modulo_gb,
        "frecuencia_mhz": frecuencia_mhz,
        "latencia_cl": especificaciones.get("latencia_cl"),
        "voltaje": especificaciones.get("voltaje"),
        "diseno": especificaciones.get("diseno"),
        "compatibilidad": especificaciones.get("compatibilidad"),
        "color": especificaciones.get("color"),
        "disipador": especificaciones.get("disipador"),
        "fuente": especificaciones.get("fuente"),
    }

    return especificaciones_limpias


def limpiar_distribucion_valoraciones(producto_detalle):
    opiniones = producto_detalle.get("opiniones") or {}
    desglose = opiniones.get("desglose_estrellas") or {}

    distribucion_limpia = {
        "producto_id": producto_detalle.get("id"),
        "estrellas_5": desglose.get("estrellas_5", 0),
        "estrellas_4": desglose.get("estrellas_4", 0),
        "estrellas_3": desglose.get("estrellas_3", 0),
        "estrellas_2": desglose.get("estrellas_2", 0),
        "estrellas_1": desglose.get("estrellas_1", 0),
        "fuente_desglose": opiniones.get("fuente_desglose"),
    }

    return distribucion_limpia


def limpiar_resenas(producto_detalle):
    resenas_limpias = []

    for posicion, resena in enumerate(producto_detalle.get("resenas") or [], start=1):
        resena_limpia = {
            "resena_id": f"{producto_detalle.get('id')}_{posicion}",
            "producto_id": producto_detalle.get("id"),
            "valoracion": resena.get("valoracion"),
            "fecha_resena_texto": resena.get("fecha_resena_texto"),
            "variante_modelo": resena.get("variante_modelo"),
            "texto_resena": resena.get("texto_resena"),
            "pros": resena.get("pros"),
            "contras": resena.get("contras"),
            "likes": resena.get("likes"),
            "numero_respuestas": resena.get("numero_respuestas"),
        }

        resenas_limpias.append(resena_limpia)

    return resenas_limpias


def preparar_datos_limpios():
    listado = leer_json(RUTA_LISTADO)
    detalle = leer_json(RUTA_DETALLE)

    productos_listado = listado.get("productos", [])
    productos_detalle = detalle.get("productos", [])

    detalle_por_id = {}

    for producto_detalle in productos_detalle:
        producto_id = producto_detalle.get("id")
        detalle_por_id[producto_id] = producto_detalle

    productos_limpios = []
    especificaciones_limpias = []
    distribuciones_limpias = []
    resenas_limpias = []

    for producto_listado in productos_listado:
        producto_id = producto_listado.get("id")
        producto_detalle = detalle_por_id.get(producto_id)

        producto_limpio = limpiar_producto(producto_listado, producto_detalle)
        productos_limpios.append(producto_limpio)

        if producto_detalle:
            especificacion_limpia = limpiar_especificaciones(producto_detalle)
            distribucion_limpia = limpiar_distribucion_valoraciones(producto_detalle)
            resenas_producto = limpiar_resenas(producto_detalle)

            especificaciones_limpias.append(especificacion_limpia)
            distribuciones_limpias.append(distribucion_limpia)
            resenas_limpias.extend(resenas_producto)

    datos_limpios = {
        "productos": productos_limpios,
        "especificaciones": especificaciones_limpias,
        "distribuciones": distribuciones_limpias,
        "resenas": resenas_limpias,
    }

    return datos_limpios


def validar_resultados(datos_limpios):
    assert len(datos_limpios["productos"]) == 1646
    assert len(datos_limpios["especificaciones"]) == 1574
    assert len(datos_limpios["distribuciones"]) == 1574

    productos_con_id = [
        producto
        for producto in datos_limpios["productos"]
        if producto.get("producto_id")
    ]

    assert len(productos_con_id) == len(
        datos_limpios["productos"]
    )

    assert all(
        especificacion.get("capacidad_gb") is None
        or capacidad_es_valida(
            especificacion.get("capacidad_gb")
        )
        for especificacion in datos_limpios["especificaciones"]
    )

    assert all(
        especificacion.get("capacidad_por_modulo_gb") is None
        or capacidad_es_valida(
            especificacion.get("capacidad_por_modulo_gb")
        )
        for especificacion in datos_limpios["especificaciones"]
    )

    texto_completo = json.dumps(
        datos_limpios,
        ensure_ascii=False,
    )

    assert "Ã" not in texto_completo
    assert "Â" not in texto_completo
    assert "â" not in texto_completo


def main():
    datos_limpios = preparar_datos_limpios()
    validar_resultados(datos_limpios)

    guardar_json(
        datos_limpios["productos"],
        RUTA_SALIDA / "productos_ram_limpios.json"
    )

    guardar_json(
        datos_limpios["especificaciones"],
        RUTA_SALIDA / "especificaciones_ram_limpias.json"
    )

    guardar_json(
        datos_limpios["distribuciones"],
        RUTA_SALIDA / "distribucion_valoraciones_ram_limpia.json"
    )

    guardar_json(
        datos_limpios["resenas"],
        RUTA_SALIDA / "resenas_ram_limpias.json"
    )

    print("Limpieza RAM completada")
    print(f"Productos: {len(datos_limpios['productos'])}")
    print(f"Especificaciones: {len(datos_limpios['especificaciones'])}")
    print(f"Distribuciones: {len(datos_limpios['distribuciones'])}")
    print(f"Resenas: {len(datos_limpios['resenas'])}")


if __name__ == "__main__":
    main()
