import os

import altair as alt
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

NOMBRES_COLUMNAS = {
    "producto_id": "ID",
    "nombre": "Producto",
    "marca": "Marca",
    "categoria": "Categoría",
    "precio": "Precio (€)",
    "valoracion_media": "Valoración (0-5)",
    "total_opiniones": "Opiniones",
    "porcentaje_positivo": "Reseñas positivas (%)",
    "total_productos": "Productos",
    "precio_medio": "Precio medio (€)",
}

NOMBRES_CATEGORIAS = {
    "memoria_ram": "Memoria RAM",
    "tarjeta_grafica": "Tarjeta gráfica",
}

NOMBRES_SENTIMIENTO = {
    "negativo": "Negativa",
    "neutral": "Neutral",
    "positivo": "Positiva",
}


def obtener_datos(ruta, params=None):
    try:
        response = requests.get(
            f"{API_BASE_URL}{ruta}",
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        st.error("No se pudo conectar con FastAPI.")
        return None


def preparar_tabla(filas):
    datos = pd.DataFrame(filas)

    if "categoria" in datos.columns:
        datos["categoria"] = datos["categoria"].replace(NOMBRES_CATEGORIAS)

    return datos.rename(columns=NOMBRES_COLUMNAS)


def nombre_grupo_legible(nombre):
    nombres = {
        "alta_gama": "Alta gama",
        "gama_media": "Gama media",
        "ficha_incompleta": "Ficha incompleta",
    }
    return nombres.get(nombre, nombre.replace("_", " "))


def grafica_barras_horizontales(
    datos,
    columna_texto,
    columna_valor,
    titulo_texto,
    titulo_valor,
    maximo=None,
):
    datos = pd.DataFrame(datos)
    escala = alt.Scale(domain=[0, maximo]) if maximo else alt.Scale(zero=True)

    return alt.Chart(datos).mark_bar(
        color="#4C78A8",
    ).encode(
        y=alt.Y(
            f"{columna_texto}:N",
            title=titulo_texto,
            sort="-x",
            axis=alt.Axis(labelLimit=240),
        ),
        x=alt.X(
            f"{columna_valor}:Q",
            title=titulo_valor,
            scale=escala,
            axis=alt.Axis(tickCount=6, format="~s"),
        ),
        tooltip=[
            alt.Tooltip(f"{columna_texto}:N", title=titulo_texto),
            alt.Tooltip(f"{columna_valor}:Q", title=titulo_valor, format=",d"),
        ],
    ).properties(
        height=max(200, len(datos) * 28),
    )


st.set_page_config(page_title="PC Componentes", layout="wide")
st.title("PC Componentes")

tab1, tab2, tab3 = st.tabs(["Asistente", "Análisis", "Recomendador"])

with tab1:
    st.write("## Asistente de compras")
    st.write("### Preguntas sobre un producto")

    busqueda_asistente = st.text_input(
        "Busca un producto por nombre",
        key="busqueda_asistente",
    )

    if len(busqueda_asistente.strip()) >= 3:
        productos_asistente = obtener_datos(
            "/consulta",
            params={"texto": busqueda_asistente.strip(), "limit": 20},
        )

        if productos_asistente:
            opciones_asistente = {
                f"{producto['nombre']} ({producto['producto_id']})": producto["producto_id"]
                for producto in productos_asistente
            }

            producto_asistente = st.selectbox(
                "Producto",
                opciones_asistente,
                key="producto_asistente",
            )

            pregunta = st.text_input(
                "Pregunta",
                placeholder="Ejemplo: ¿Cuáles son las quejas más comunes?",
            )

            if st.button("Preguntar"):
                if len(pregunta.strip()) < 3:
                    st.warning("Escribe una pregunta un poco más larga.")
                else:
                    respuesta = obtener_datos(
                        "/ask",
                        params={
                            "producto_id": opciones_asistente[producto_asistente],
                            "pregunta": pregunta.strip(),
                        },
                    )

                    if respuesta:
                        st.info(respuesta["respuesta"])

                        if respuesta["tipo_respuesta"] == "recomendacion":
                            st.dataframe(
                                preparar_tabla(respuesta["datos"]),
                                width="stretch",
                                hide_index=True,
                            )

    elif busqueda_asistente:
        st.info("Escribe al menos tres caracteres para buscar.")

    st.divider()
    st.write("### Filtro del catálogo")
    st.write("Filtra productos por categoría, marca y precio.")

    categorias = {
        "Todas": None,
        "Memoria RAM": "memoria_ram",
        "Tarjeta gráfica": "tarjeta_grafica",
    }

    categoria = st.selectbox("Categoría", categorias)
    marca = st.text_input("Marca")
    precio_min = st.number_input("Precio mínimo", min_value=0.0)
    precio_max = st.number_input("Precio máximo", min_value=0.0)
    orden = st.selectbox(
        "Ordenar por",
        ["precio", "valoracion", "opiniones"],
    )

    if st.button("Búsqueda"):
        if precio_max > 0 and precio_min > precio_max:
            st.warning("El precio mínimo no puede superar al máximo.")
        else:
            parametros = {
                "orden": orden,
                "limit": 20,
            }

            if categorias[categoria]:
                parametros["categoria"] = categorias[categoria]

            if marca.strip():
                parametros["marca"] = marca.strip()

            if precio_min > 0:
                parametros["precio_min"] = precio_min

            if precio_max > 0:
                parametros["precio_max"] = precio_max

            productos = obtener_datos("/consulta", params=parametros)

            if productos:
                st.dataframe(
                    preparar_tabla(productos),
                    width="stretch",
                    hide_index=True,
                )
            elif productos is not None:
                st.warning("No se encontraron productos.")

with tab2:
    st.write("## Análisis")
    st.write("Consulta el sentimiento y los comentarios de un producto.")

    busqueda_analisis = st.text_input(
        "Busca un producto para analizar",
        key="busqueda_analisis",
    )

    if len(busqueda_analisis.strip()) >= 3:
        productos_analisis = obtener_datos(
            "/consulta",
            params={"texto": busqueda_analisis.strip(), "limit": 20},
        )

        if productos_analisis:
            opciones_analisis = {
                f"{producto['nombre']} ({producto['producto_id']})": producto["producto_id"]
                for producto in productos_analisis
            }

            producto_analisis = st.selectbox(
                "Producto para analizar",
                opciones_analisis,
            )

            if st.button("Analizar producto"):
                analisis = obtener_datos(
                    "/sentiment",
                    params={
                        "producto_id": opciones_analisis[producto_analisis],
                    },
                )

                if analisis:
                    st.write(f"**Reseñas analizadas:** {analisis['total_resenas']}")

                    st.write("### Sentimiento")
                    datos_sentimiento = pd.DataFrame(analisis["sentimientos"])
                    datos_sentimiento["opinion"] = (
                        datos_sentimiento["sentimiento"].replace(NOMBRES_SENTIMIENTO)
                    )
                    grafica_sentimiento = alt.Chart(datos_sentimiento).mark_bar().encode(
                        x=alt.X(
                            "opinion:N",
                            title="Tipo de opinión",
                            sort=["Negativa", "Neutral", "Positiva"],
                        ),
                        y=alt.Y(
                            "porcentaje:Q",
                            title="Porcentaje de reseñas (%)",
                            scale=alt.Scale(domain=[0, 100]),
                            axis=alt.Axis(tickCount=6),
                        ),
                        color=alt.Color(
                            "opinion:N",
                            legend=None,
                            scale=alt.Scale(
                                domain=["Negativa", "Neutral", "Positiva"],
                                range=["#F58518", "#F2CF5B", "#4C78A8"],
                            ),
                        ),
                        tooltip=[
                            alt.Tooltip("opinion:N", title="Opinión"),
                            alt.Tooltip(
                                "porcentaje:Q",
                                title="Porcentaje",
                                format=".1f",
                            ),
                            alt.Tooltip("total:Q", title="Reseñas", format=",d"),
                        ],
                    ).properties(height=350)
                    st.altair_chart(grafica_sentimiento, width="stretch")

                    st.write("### Palabras clave")
                    grafica_palabras = grafica_barras_horizontales(
                        analisis["palabras_clave"],
                        "palabra",
                        "total",
                        "Palabra",
                        "Número de apariciones",
                    )
                    st.altair_chart(grafica_palabras, width="stretch")

                    columna_pros, columna_contras = st.columns(2)

                    with columna_pros:
                        st.write("### Pros")
                        if analisis["pros"]:
                            for pro in analisis["pros"]:
                                st.write(f"- {pro}")
                        else:
                            st.write("No hay pros escritos.")

                    with columna_contras:
                        st.write("### Contras")
                        if analisis["contras"]:
                            for contra in analisis["contras"]:
                                st.write(f"- {contra}")
                        else:
                            st.write("No hay contras escritos.")

    elif busqueda_analisis:
        st.info("Escribe al menos tres caracteres para buscar.")

    st.divider()
    st.write("### Resumen general")

    resumen = obtener_datos("/graficas/resumen")

    if resumen:
        st.dataframe(
            preparar_tabla(resumen),
            width="stretch",
            hide_index=True,
        )

with tab3:
    st.write("## Recomendador")
    st.write("Busca productos parecidos del mismo grupo.")

    busqueda_recomendador = st.text_input(
        "Busca un producto de referencia",
        key="busqueda_recomendador",
    )

    if len(busqueda_recomendador.strip()) >= 3:
        productos_recomendador = obtener_datos(
            "/consulta",
            params={"texto": busqueda_recomendador.strip(), "limit": 20},
        )

        if productos_recomendador:
            opciones_recomendador = {
                f"{producto['nombre']} ({producto['producto_id']})": producto["producto_id"]
                for producto in productos_recomendador
            }

            producto_recomendador = st.selectbox(
                "Producto de referencia",
                opciones_recomendador,
            )

            if st.button("Buscar alternativas"):
                recomendaciones = obtener_datos(
                    "/similar-products",
                    params={
                        "producto_id": opciones_recomendador[producto_recomendador],
                        "limit": 5,
                    },
                )

                if recomendaciones:
                    origen = recomendaciones["producto_origen"]
                    st.write(f"**Grupo:** {origen['nombre_grupo']}")
                    st.dataframe(
                        preparar_tabla(recomendaciones["similares"]),
                        width="stretch",
                        hide_index=True,
                    )

    elif busqueda_recomendador:
        st.info("Escribe al menos tres caracteres para buscar.")

    st.write("### Mapa interactivo de clústeres")
    st.write("Cada punto representa un producto y cada color representa un grupo.")

    categorias_mapa = {
        "Memoria RAM": "memoria_ram",
        "Tarjetas gráficas": "tarjeta_grafica",
    }
    categoria_mapa = st.selectbox(
        "Categoría del mapa",
        categorias_mapa,
        key="categoria_mapa",
    )

    if st.button("Mostrar mapa PCA"):
        mapa = obtener_datos(
            "/modelos/pca",
            params={"categoria": categorias_mapa[categoria_mapa]},
        )

        if mapa:
            datos_mapa = pd.DataFrame(mapa["productos"])
            datos_mapa["grupo_visible"] = datos_mapa["nombre_grupo"].apply(
                nombre_grupo_legible
            )
            grafica = alt.Chart(datos_mapa).mark_circle(
                size=60,
                opacity=0.7,
            ).encode(
                x=alt.X(
                    "pca_1:Q",
                    title="Eje 1: resumen principal",
                    axis=alt.Axis(tickCount=6, format=".1f", grid=True),
                ),
                y=alt.Y(
                    "pca_2:Q",
                    title="Eje 2: resumen secundario",
                    axis=alt.Axis(tickCount=6, format=".1f", grid=True),
                ),
                color=alt.Color(
                    "grupo_visible:N",
                    title="Grupo",
                    scale=alt.Scale(range=["#4C78A8", "#F2CF5B", "#F58518"]),
                ),
                shape=alt.Shape("grupo_visible:N", legend=None),
                tooltip=[
                    alt.Tooltip("nombre:N", title="Producto"),
                    alt.Tooltip("producto_id:N", title="ID"),
                    alt.Tooltip("grupo_visible:N", title="Grupo"),
                    alt.Tooltip("precio:Q", title="Precio (€)", format=".2f"),
                ],
            ).properties(
                title="Mapa de similitud entre productos",
                height=430,
            ).interactive()

            st.caption(
                f"Productos representados: {mapa['total_productos']}. "
                "Cómo leer el mapa: los productos cercanos tienen características "
                "parecidas y el color indica su grupo. Los números de los ejes "
                "solo sirven para colocar los puntos; no son euros, GB ni rendimiento."
            )
            st.altair_chart(grafica, width="stretch")

    st.divider()
    st.write("### Resumen general de modelos")

    clustering = obtener_datos("/modelos/clustering")
    sentimiento = obtener_datos("/modelos/sentimiento")

    if clustering:
        st.write("### Clustering")
        st.caption("Los gráficos de RAM y tarjetas gráficas usan la misma escala.")

        clustering_ram = pd.DataFrame(clustering["ram"])
        clustering_gpu = pd.DataFrame(clustering["gpu"])

        clustering_ram["grupo_visible"] = clustering_ram["nombre_grupo"].apply(
            nombre_grupo_legible
        )
        clustering_gpu["grupo_visible"] = clustering_gpu["nombre_grupo"].apply(
            nombre_grupo_legible
        )
        maximo_clustering = max(
            clustering_ram["total"].max(),
            clustering_gpu["total"].max(),
        ) * 1.05

        columna_ram, columna_gpu = st.columns(2)

        with columna_ram:
            st.write("RAM")
            grafica_clustering_ram = grafica_barras_horizontales(
                clustering_ram,
                "grupo_visible",
                "total",
                "Grupo de productos",
                "Número de productos",
                maximo_clustering,
            )
            st.altair_chart(grafica_clustering_ram, width="stretch")

        with columna_gpu:
            st.write("Tarjetas gráficas")
            grafica_clustering_gpu = grafica_barras_horizontales(
                clustering_gpu,
                "grupo_visible",
                "total",
                "Grupo de productos",
                "Número de productos",
                maximo_clustering,
            )
            st.altair_chart(grafica_clustering_gpu, width="stretch")

    if sentimiento:
        st.write("### Sentimiento")
        st.caption("Los gráficos de RAM y tarjetas gráficas usan la misma escala.")

        sentimiento_ram = pd.DataFrame(sentimiento["ram"])
        sentimiento_gpu = pd.DataFrame(sentimiento["gpu"])
        sentimiento_ram["opinion"] = sentimiento_ram["sentimiento"].replace(
            NOMBRES_SENTIMIENTO
        )
        sentimiento_gpu["opinion"] = sentimiento_gpu["sentimiento"].replace(
            NOMBRES_SENTIMIENTO
        )
        maximo_sentimiento = max(
            sentimiento_ram["total"].max(),
            sentimiento_gpu["total"].max(),
        ) * 1.05

        columna_ram, columna_gpu = st.columns(2)

        with columna_ram:
            st.write("RAM")
            grafica_sentimiento_ram = grafica_barras_horizontales(
                sentimiento_ram,
                "opinion",
                "total",
                "Opinión",
                "Número de reseñas",
                maximo_sentimiento,
            )
            st.altair_chart(grafica_sentimiento_ram, width="stretch")

        with columna_gpu:
            st.write("Tarjetas gráficas")
            grafica_sentimiento_gpu = grafica_barras_horizontales(
                sentimiento_gpu,
                "opinion",
                "total",
                "Opinión",
                "Número de reseñas",
                maximo_sentimiento,
            )
            st.altair_chart(grafica_sentimiento_gpu, width="stretch")
