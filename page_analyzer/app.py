import psycopg2
import requests
from bs4 import BeautifulSoup
from flask import Flask, flash, redirect, render_template, request, url_for
from psycopg2.extras import RealDictCursor

from .config import Config
from .validator import validate_url

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config.get("SECRET_KEY")


def get_db_connection():
    return psycopg2.connect(app.config.get("DATABASE_URL"),
                            cursor_factory=RealDictCursor)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        errors = validate_url(url)
        if errors:
            for err in errors:
                flash(err, "error")
            return render_template('index.html')

        conn = get_db_connection()
        with conn.cursor() as curs:
            curs.execute("SELECT id FROM urls WHERE name = %s", (url,))
            existing_url = curs.fetchone()
            if existing_url:
                flash("Страница уже существует", "error")
                conn.close()
                return redirect(url_for('url_show', id=existing_url["id"]))

            curs.execute(
                "INSERT INTO urls (name) VALUES (%s) RETURNING id", (url,))
            new_id = curs.fetchone()["id"]
            conn.commit()
        conn.close()

        flash("URL успешно добавлен", "success")
        return redirect(url_for('url_show', id=new_id))

    return render_template('index.html')


@app.route('/urls', methods=['GET'])
def urls():
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
    return render_template('urls.html', urls=urls_data)


@app.route('/urls/<int:id>', methods=['GET'])
def url_show(id):
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
    return render_template('url.html', url=url, checks=checks)


@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_checks(id):
    conn = get_db_connection()
    with conn.cursor() as curs:
        curs.execute("SELECT * FROM urls WHERE id = %s", (id,))
        url = curs.fetchone()
        if url is None:
            flash("URL не найден", "error")
            conn.close()
            return redirect(url_for('urls'))

        try:
            response = requests.get(url["name"])
            response.raise_for_status()
        except requests.RequestException:
            flash("Произошла ошибка при проверке", "error")
            conn.close()
            return redirect(url_for('url_show', id=id))

        status_code = response.status_code

        soup = BeautifulSoup(response.text, "html.parser")
        h1 = soup.find("h1")
        title = soup.find("title")
        meta = soup.find("meta", attrs={"name": "description"})

        h1_value = h1.get_text(strip=True) if h1 else None
        title_value = title.get_text(strip=True) if title else ""
        description_value = meta.get(
            "content", "").strip() if meta else None

        curs.execute(
            "INSERT INTO url_checks (url_id, status_code, h1, title,"
            "description) VALUES (%s, %s, %s, %s, %s)",
            (id, status_code, h1_value, title_value, description_value)
        )
        conn.commit()
    conn.close()
    flash("Проверка успешно создана", "success")
    return redirect(url_for('url_show', id=id))


if __name__ == "__main__":
    app.run(debug=True)
