# Este módulo contiene la función para conectar a una base de datos PostgreSQL utilizando psycopg.

import psycopg


def conectar_postgresql(database_uri):
    conn = psycopg.connect(database_uri)
    return conn