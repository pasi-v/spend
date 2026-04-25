import logging
import sqlite3

logger = logging.getLogger(__name__)


def schema() -> str:
    return """
CREATE TABLE IF NOT EXISTS stores (
store_id INTEGER PRIMARY KEY AUTOINCREMENT,
slug TEXT UNIQUE,
name TEXT);
"""


def insert_store(conn: sqlite3.Connection, slug: str, name:str) -> None:
    sql = "INSERT INTO stores (slug, name) VALUES (?, ?)"
    values = (slug.lower(), name)
    conn.execute(sql, values)


def select_stores(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    sql = "SELECT slug, name FROM stores"
    res = conn.execute(sql)
    return res.fetchall()


def select_store(conn: sqlite3.Connection, slug: str) -> sqlite3.Row | None:
    sql = "SELECT store_id, slug, name FROM stores WHERE slug = ?"
    values = (slug.lower(), )
    res = conn.execute(sql, values)
    row: sqlite3.Row | None = res.fetchone()
    return row


def update_store(conn: sqlite3.Connection, slug: str, name: str) -> None:
    sql = "UPDATE stores SET name = ? WHERE slug = ?"
    values = (name, slug.lower())
    conn.execute(sql, values)


def delete_store(conn: sqlite3.Connection, slug: str) -> None:
    sql = "DELETE FROM stores WHERE slug = ?"
    values = (slug.lower(), )
    conn.execute(sql, values)


def do_add_store(conn: sqlite3.Connection, slug: str, name: str) -> None:
    """Add store to the database."""
    print(f"Adding {slug} to database and setting name={name}")
    insert_store(conn, slug, name)


def do_list_stores(conn: sqlite3.Connection) -> None:
    """List all stores in the database."""
    stores = select_stores(conn)
    for store in stores:
        print(f'{store["slug"]}: {store["name"]}')


def do_show_store(conn: sqlite3.Connection, slug: str) -> None:
    """Show one store identified by slug."""
    store = select_store(conn, slug)
    if store is not None:
        print(f'{store["slug"]}: {store["name"]}')
    else:
        logger.warning("Store %s not found.", slug)


def do_update_store(conn: sqlite3.Connection, slug: str) -> None:
    """Input name of store with slug and update it in the database."""
    store = select_store(conn, slug)
    if store is not None:
        name = input(f"Enter new name for {slug}: ")
        update_store(conn, slug, name)
    else:
        logger.warning("Store %s not found.", slug)


def do_delete_store(conn: sqlite3.Connection, slug: str) -> None:
    """Delete store <slug> from the database."""
    delete_store(conn, slug)


def require_store(conn: sqlite3.Connection, slug: str) -> sqlite3.Row:
    """Return store or raise a ValueError if not found."""
    store = select_store(conn, slug)
    if store is None:
        raise ValueError(f"Unknown store: {slug}")
    return store
