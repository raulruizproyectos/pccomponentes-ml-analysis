"""Comprueba que las cargas repetidas no fallen por datos existentes."""

from database.inserciones_gpu import (
    insertar_distribucion_valoraciones_gpu,
    insertar_especificaciones_gpu,
    insertar_productos_gpu,
    insertar_resenas_gpu,
)
from database.inserciones_ram import (
    insertar_distribucion_valoraciones,
    insertar_especificaciones_ram,
    insertar_productos_ram,
    insertar_resenas_ram,
)


class CursorPrueba:
    def __init__(self, consultas):
        self.consultas = consultas

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def executemany(self, consulta, datos):
        self.consultas.append(consulta)


class ConexionPrueba:
    def __init__(self):
        self.consultas = []

    def cursor(self):
        return CursorPrueba(self.consultas)


def main():
    conexion = ConexionPrueba()
    funciones = [
        insertar_productos_ram,
        insertar_especificaciones_ram,
        insertar_distribucion_valoraciones,
        insertar_resenas_ram,
        insertar_productos_gpu,
        insertar_especificaciones_gpu,
        insertar_distribucion_valoraciones_gpu,
        insertar_resenas_gpu,
    ]

    for funcion in funciones:
        funcion(conexion, [])

    assert len(conexion.consultas) == len(funciones)
    assert all("ON CONFLICT" in consulta for consulta in conexion.consultas)
    print("ETL: comprobacion de actualizaciones correcta")


if __name__ == "__main__":
    main()
