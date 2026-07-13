from pathlib import Path


app = Path(__file__).parent / "streamlit_app" / "streamlit_main.py"
source = app.read_text(encoding="utf-8")

compile(source, str(app), "exec")

for forbidden in ("DATABASE_URL", "postgresql://", "psycopg", "rds.amazonaws.com"):
    assert forbidden.lower() not in source.lower(), f"Contenido no permitido: {forbidden}"

for route in (
    "/consulta",
    "/ask",
    "/sentiment",
    "/similar-products",
    "/modelos/pca",
    "/graficas/resumen",
    "/modelos/clustering",
    "/modelos/sentimiento",
):
    assert route in source, f"Falta la ruta: {route}"

for text in (
    "Cómo leer el mapa",
    "Porcentaje de reseñas (%)",
    "Número de apariciones",
    "Número de productos",
    "Número de reseñas",
):
    assert text in source, f"Falta el texto visible: {text}"

print("Streamlit: comprobación correcta")
