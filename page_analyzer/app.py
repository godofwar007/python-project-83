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


def query_db(query, params=(), commit=False, one=False):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(query, params)
        if commit:
            conn.commit()
            result = None
        else:
            result = cur.fetchone() if one else cur.fetchall()
    conn.close()
    return result


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
    curs.close()
    conn.close()
    if url is None:
        flash("URL не найден", "error")
        return redirect(url_for('urls'))
    return render_template('url.html', url=url)


if __name__ == "__main__":
    app.run(debug=True)
