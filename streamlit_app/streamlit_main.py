import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"


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


st.set_page_config(page_title="PC Componentes", layout="wide")
st.title("PC Componentes")

tab1, tab2, tab3 = st.tabs(["Asistente", "Análisis", "Recomendador"])

with tab1:
    st.write("## Asistente de compras")
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
                    productos,
                    width="stretch",
                    hide_index=True,
                )
            elif productos is not None:
                st.warning("No se encontraron productos.")

with tab2:
    st.write("## Análisis")
    st.write("Aquí va una descripción hecha por Andrés")

    resumen = obtener_datos("/graficas/resumen")

    if resumen:
        st.dataframe(
            resumen,
            width="stretch",
            hide_index=True,
        )

with tab3:
    st.write("## Recomendador")
    st.write("Resultados generales de clustering y sentimiento.")

    clustering = obtener_datos("/modelos/clustering")
    sentimiento = obtener_datos("/modelos/sentimiento")

    if clustering:
        st.write("### Clustering")

        columna_ram, columna_gpu = st.columns(2)

        with columna_ram:
            st.write("RAM")
            st.bar_chart(
                clustering["ram"],
                x="nombre_grupo",
                y="total",
                horizontal=True,
            )

        with columna_gpu:
            st.write("Tarjetas gráficas")
            st.bar_chart(
                clustering["gpu"],
                x="nombre_grupo",
                y="total",
                horizontal=True,
            )

    if sentimiento:
        st.write("### Sentimiento")

        columna_ram, columna_gpu = st.columns(2)

        with columna_ram:
            st.write("RAM")
            st.bar_chart(
                sentimiento["ram"],
                x="sentimiento",
                y="total",
                horizontal=True,
            )

        with columna_gpu:
            st.write("Tarjetas gráficas")
            st.bar_chart(
                sentimiento["gpu"],
                x="sentimiento",
                y="total",
                horizontal=True,
            )
