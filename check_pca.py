import pandas as pd

from api.main import calcular_coordenadas_pca


datos = pd.DataFrame({
    "precio": [50, 75, 300, 500],
    "capacidad": [8, 16, 32, 64],
    "tipo": ["DDR4", "DDR4", "DDR5", "DDR5"],
})

resultado = calcular_coordenadas_pca(
    datos,
    ["precio", "capacidad"],
    ["tipo"],
)

assert len(resultado) == 4
assert resultado[["pca_1", "pca_2"]].notna().all().all()

print("PCA: comprobacion correcta")
