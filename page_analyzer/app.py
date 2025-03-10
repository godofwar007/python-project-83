import os

import requests
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from .db import (
    add_tags,
    get_db_connection,
    get_url,
    get_url_by_id,
    get_urls,
    url_check,
)
from .parsing import parse_url
from .validator import normalize_url, validate_url

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['DATABASE_URL'] = DATABASE_URL


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/urls', methods=['POST'])
def create_url():
    url = request.form.get('url')
    url = normalize_url(url)
    errors = validate_url(url)
    if errors:
        for err in errors:
            flash(err, "error")
        return render_template('index.html'), 422
    connection = get_db_connection()
    url_id = get_url(url, connection)

    return redirect(url_for('url_show', id=url_id))


@app.route('/urls', methods=['GET'])
def urls():
    connection = get_db_connection()
    urls_data = get_urls(connection)
    return render_template('urls.html', urls=urls_data)


@app.route('/urls/<int:id>', methods=['GET'])
def url_show(id):
    connection = get_db_connection()
    checks, url = get_url_by_id(id, connection)
    return render_template('url.html', url=url, checks=checks)


@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_checks(id):
    connection = get_db_connection()
    url = url_check(id, connection)
    try:
        response = requests.get(url["name"])
        response.raise_for_status()
    except requests.RequestException:
        flash("Произошла ошибка при проверке", "error")
        return redirect(url_for('url_show', id=id))

    status_code, h1_value, title_value, description_value = parse_url(response)
    connection = get_db_connection()
    add_tags(id, status_code, h1_value, title_value,
             description_value, connection)

    flash("Страница успешно проверена", "success")
    return redirect(url_for('url_show', id=id))


if __name__ == "__main__":
    app.run(debug=True)
