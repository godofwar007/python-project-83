import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_default_secret_key')
    DATABASE_URL = os.getenv(
        'DATABASE_URL', 'postgresql://user:password@localhost/dbname')
