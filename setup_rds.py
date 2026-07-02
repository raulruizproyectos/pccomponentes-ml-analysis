"""Crea la BD y aplica esquema en RDS."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import psycopg

DATABASE_URL = os.getenv("DATABASE_URL", "")
POSTGRES_URL = DATABASE_URL.replace("/pccomponentes_ml", "/postgres")
TARGET_URL = DATABASE_URL
ESQUEMA = Path(__file__).parent / "database" / "esquema.sql"


def main():
    with psycopg.connect(POSTGRES_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = 'pccomponentes_ml'")
            if cur.fetchone():
                print("BD pccomponentes_ml ya existe")
            else:
                cur.execute("CREATE DATABASE pccomponentes_ml")
                print("BD pccomponentes_ml creada")

    sql = ESQUEMA.read_text(encoding="utf-8")
    with psycopg.connect(TARGET_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    print("Esquema aplicado")

    with psycopg.connect(TARGET_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
            tablas = [r[0] for r in cur.fetchall()]
    print(f"Tablas: {tablas}")


if __name__ == "__main__":
    main()