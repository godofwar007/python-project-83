import psycopg2
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
        curs = conn.cursor()

        curs.execute("SELECT id FROM urls WHERE name = %s", (url,))
        existing_url = curs.fetchone()
        if existing_url:
            flash("Такой URL уже существует", "error")
            curs.close()
            conn.close()
            return render_template('index.html')

        curs.execute("INSERT INTO urls (name) VALUES (%s)", (url,))
        conn.commit()
        curs.close()
        conn.close()

        flash("URL успешно добавлен", "success")
        return redirect(url_for('urls'))
    return render_template('index.html')


@app.route('/urls', methods=['GET'])
def urls():
    conn = get_db_connection()
    curs = conn.cursor()
    curs.execute("SELECT * FROM urls ORDER BY created_at DESC")
    urls = curs.fetchall()
    curs.close()
    conn.close()
    return render_template('urls.html', urls=urls)


@app.route('/urls/<int:id>', methods=['GET'])
def url_show(id):
    conn = get_db_connection()
    curs = conn.cursor()
    curs.execute("SELECT * FROM urls WHERE id = %s", (id,))
    url = curs.fetchone()
    if url is None:
        flash("URL не найден", "error")
        curs.close()
        conn.close()
        return redirect(url_for('urls'))

    curs.execute(
        "SELECT id, created_at FROM url_checks WHERE url_id = %s "
        "ORDER BY created_at DESC", (id,))
    checks = curs.fetchall()
    curs.close()
    conn.close()
    return render_template('url.html', url=url, checks=checks)


@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_checks(id):
    conn = get_db_connection()
    curs = conn.cursor()
    curs.execute("SELECT * FROM urls WHERE id = %s", (id,))
    url = curs.fetchone()
    if url is None:
        flash("URL не найден", "error")
        curs.close()
        conn.close()
        return redirect(url_for('urls'))

    curs.execute("INSERT INTO url_checks (url_id) VALUES (%s)", (id,))
    conn.commit()
    curs.close()
    conn.close()
    flash("Проверка успешно создана", "success")
    return redirect(url_for('url_show', id=id))


if __name__ == "__main__":
    app.run(debug=True)
