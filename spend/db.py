import sqlite3

from . import producers, products, stores, vouchers


def get_connection(dbname: str) -> sqlite3.Connection:
    conn = sqlite3.connect(dbname)
    conn.execute("PRAGMA foreign_keys = 1")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(producers.schema())
    conn.executescript(products.schema())
    conn.executescript(stores.schema())
    conn.executescript(vouchers.schema())
