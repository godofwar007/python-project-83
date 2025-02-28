from flask import Flask
# import psycopg2
from .config import Config

app = Flask(__name__)
app.config.from_object(Config)

# conn = psycopg2.connect(app.config['DATABASE_URL'])


@app.route('/')
def index():
    return "Hello, Page Analyzer!"


if __name__ == "__main__":
    app.run(debug=True)
