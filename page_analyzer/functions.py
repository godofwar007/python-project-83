import psycopg2
from bs4 import BeautifulSoup
from flask import current_app, flash, redirect, url_for
from psycopg2.extras import RealDictCursor


def get_db_connection():
    database_url = current_app.config.get('DATABASE_URL')
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)


def get_url(url):
    conn = get_db_connection()
    with conn.cursor() as curs:
        curs.execute("SELECT id FROM urls WHERE name = %s", (url,))
        existing_url = curs.fetchone()
        if existing_url:
            flash("Страница уже существует", "error")
            conn.close()
            return existing_url["id"]

        curs.execute(
            "INSERT INTO urls (name) VALUES (%s) RETURNING id", (url,))
        new_id = curs.fetchone()["id"]
        flash("Страница успешно добавлена", "success")

        conn.commit()
    conn.close()
    return new_id


def get_urls():
    conn = get_db_connection()
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
    conn.close()
    return urls_data


def get_url_by_id(id):
    conn = get_db_connection()
    with conn.cursor() as curs:
        curs.execute("SELECT * FROM urls WHERE id = %s", (id,))
        url = curs.fetchone()
        if url is None:
            flash("URL не найден", "error")
            conn.close()
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
    conn.close()
    return checks, url


def parse_url(response):
    status_code = response.status_code
    soup = BeautifulSoup(response.text, "html.parser")
    h1 = soup.find("h1")
    title = soup.find("title")
    meta = soup.find("meta", attrs={"name": "description"})

    h1_value = h1.get_text(strip=True) if h1 else None
    title_value = title.get_text(strip=True) if title else ""
    description_value = meta.get("content", "").strip() if meta else None

    return status_code, h1_value, title_value, description_value
