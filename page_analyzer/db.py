from functools import wraps

import psycopg2
from flask import current_app, flash, redirect, url_for
from psycopg2.extras import RealDictCursor


def get_db_connection():
    database_url = current_app.config.get('DATABASE_URL')
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)


def connection(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with get_db_connection() as conn:
            return func(*args, conn=conn, **kwargs)
    return wrapper


@connection
def get_url(url, conn):
    with conn.cursor() as curs:
        curs.execute("SELECT id FROM urls WHERE name = %s", (url,))
        existing_url = curs.fetchone()
        if existing_url:
            flash("Страница уже существует", "error")
            return existing_url["id"]

        curs.execute(
            "INSERT INTO urls (name) VALUES (%s) RETURNING id", (url,))
        new_id = curs.fetchone()["id"]
        flash("Страница успешно добавлена", "success")

        conn.commit()
    return new_id


@connection
def get_urls(conn):
    with conn.cursor() as curs:
        curs.execute("""
            SELECT
                u.id,
                u.name,
                u.created_at,
                (
                    SELECT created_at
                    FROM url_checks
                    WHERE url_checks.url_id = u.id
                    ORDER BY created_at DESC
                    LIMIT 1
                ) AS last_check_date,
                (
                    SELECT status_code
                    FROM url_checks
                    WHERE url_checks.url_id = u.id
                    ORDER BY created_at DESC
                    LIMIT 1
                ) AS last_check_code
            FROM urls AS u
            ORDER BY u.id DESC
        """)
        urls_data = curs.fetchall()
    return urls_data


@connection
def get_url_by_id(id, conn):
    with conn.cursor() as curs:
        curs.execute("SELECT * FROM urls WHERE id = %s", (id,))
        url = curs.fetchone()
        if url is None:
            flash("URL не найден", "error")
            return redirect(url_for('urls'))

        curs.execute("""
            SELECT
                id,
                h1,
                description,
                status_code,
                title,
                created_at
            FROM url_checks
            WHERE url_id = %s
            ORDER BY created_at DESC
        """, (id,))
        checks = curs.fetchall()
    return checks, url


@connection
def url_check(id, conn):
    with conn.cursor() as curs:
        curs.execute("SELECT * FROM urls WHERE id = %s", (id,))
        url = curs.fetchone()
        if url is None:
            flash("URL не найден", "error")
            return redirect(url_for('urls'))
    return url


@connection
def add_tags(id, status_code, h1_value, title_value, description_value, conn):
    with conn.cursor() as curs:
        curs.execute(
            "INSERT INTO url_checks (url_id, status_code, h1, title, "
            "description) VALUES (%s, %s, %s, %s, %s)",
            (id, status_code, h1_value, title_value, description_value)
        )
        conn.commit()
    return redirect(url_for('url_show', id=id))
