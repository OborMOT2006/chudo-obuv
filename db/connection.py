"""Соединения PostgreSQL. Конфигурация — переменные окружения, без паролей в Git."""
import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor


def db_config():
    return {
        'host': os.environ.get('DB_HOST', '127.0.0.1'),
        'port': int(os.environ.get('DB_PORT', '5432')),
        'dbname': os.environ.get('DB_NAME', 'shoe_store'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', ''),
        'connect_timeout': 5,
    }


@contextmanager
def transaction():
    """Одна транзакция: commit при успехе, rollback при исключении."""
    conn = psycopg2.connect(**db_config())
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(query, params=()):
    with transaction() as cur:
        cur.execute(query, params)
        names = [d[0] for d in cur.description]
        return [dict(zip(names, row)) for row in cur.fetchall()]


def fetch_one(query, params=()):
    with transaction() as cur:
        cur.execute(query, params)
        if cur.description is None:
            return None
        row = cur.fetchone()
        return dict(zip([d[0] for d in cur.description], row)) if row else None


def check_connection():
    return fetch_one('SELECT version() AS version')['version']
