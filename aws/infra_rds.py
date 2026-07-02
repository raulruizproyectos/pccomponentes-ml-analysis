"""
Utilidades para PostgreSQL RDS del proyecto.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ESQUEMA_SQL = PROJECT_ROOT / "database" / "esquema.sql"


def probar_conexion(database_url: str) -> dict:
    import psycopg

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
                """
            )
            tablas = [fila[0] for fila in cursor.fetchall()]

    return {
        "conectado": True,
        "version": version,
        "tablas": tablas,
    }


def aplicar_esquema(database_url: str, ruta_esquema: Path | None = None) -> dict:
    import psycopg

    ruta = ruta_esquema or ESQUEMA_SQL
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el esquema SQL: {ruta}")

    sql = ruta.read_text(encoding="utf-8")

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
        conn.commit()

    estado = probar_conexion(database_url)
    return {
        "esquema_aplicado": True,
        "archivo": str(ruta),
        "tablas": estado["tablas"],
    }