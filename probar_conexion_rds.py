"""Prueba rápida de conexión a RDS PostgreSQL."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def main() -> int:
    database_url = os.getenv("DATABASE_URL", "")

    if not database_url or "TU_PASSWORD" in database_url:
        print("Edita .env y sustituye TU_PASSWORD por la contraseña real de postgres.")
        return 1

    try:
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

        print("Conexion OK")
        print(f"PostgreSQL: {version[:80]}...")
        print(f"Tablas existentes: {tablas if tablas else '(ninguna — ejecuta esquema.sql)'}")
        return 0
    except Exception as error:
        print(f"Error de conexion: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())