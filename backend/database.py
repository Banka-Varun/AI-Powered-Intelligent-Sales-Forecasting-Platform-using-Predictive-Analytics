import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def configured_url():
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    if os.getenv('DATABASE_URL'):
        return os.environ['DATABASE_URL']
    password = os.getenv('DB_PASSWORD')
    if not password or password == 'replace_with_your_local_password':
        raise RuntimeError('Copy .env.example to .env and set your PostgreSQL password first.')
    # URL.create handles special characters in a password without manual escaping.
    return URL.create('postgresql+psycopg', username=os.getenv('DB_USER', 'postgres'),
                      password=password, host=os.getenv('DB_HOST', 'localhost'),
                      port=int(os.getenv('DB_PORT', '5432')),
                      database=os.getenv('DB_NAME', 'salesgenie'))


def make_engine(url):
    is_sqlite = str(url).startswith('sqlite')
    args = {'check_same_thread': False} if is_sqlite else {'connect_timeout': 5}
    return create_engine(url, connect_args=args, pool_pre_ping=True)
