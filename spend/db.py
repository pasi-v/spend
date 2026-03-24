import sqlite3
import producers
import products
import stores

def get_connection(dbname: str="spend.db"):
    conn = sqlite3.connect(dbname)
    conn.execute("PRAGMA foreign_keys = 1")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn):
    conn.executescript(producers.schema())
    conn.executescript(products.schema())
    conn.executescript(stores.schema())
