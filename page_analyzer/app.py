from flask import Flask, render_template

# import psycopg2
from .config import Config

app = Flask(__name__)
app.config.from_object(Config)

# conn = psycopg2.connect(app.config['DATABASE_URL'])


@app.route('/')
def index():
    text = 'Мой первый что-то в проекте'
    return render_template('index.html', text=text)


if __name__ == "__main__":
    app.run(debug=True)
