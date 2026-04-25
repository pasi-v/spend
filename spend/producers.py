import logging
import sqlite3

logger = logging.getLogger(__name__)


def schema() -> str:
    return """
CREATE TABLE IF NOT EXISTS producers (
producer_id INTEGER PRIMARY KEY AUTOINCREMENT,
slug TEXT UNIQUE,
name TEXT
);

CREATE INDEX IF NOT EXISTS idx_producers_slug 
ON producers(slug)"""


def insert_producer(conn: sqlite3.Connection, slug: str, name: str) -> None:
    sql = "INSERT INTO producers (slug, name) VALUES (?, ?)"
    values = (slug.lower(), name)
    conn.execute(sql, values)


def select_producers(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    sql = "SELECT slug, name FROM producers"
    res = conn.execute(sql)
    return res.fetchall()


def select_producer(conn: sqlite3.Connection, slug: str) -> sqlite3.Row | None:
    sql = "SELECT producer_id, slug, name FROM producers WHERE slug = ?"
    values = (slug.lower(), )
    res = conn.execute(sql, values)
    row: sqlite3.Row | None = res.fetchone()
    return row


def update_producer(conn: sqlite3.Connection, slug: str, name: str) -> None:
    sql = "UPDATE producers SET name = ? WHERE slug = ?"
    values = (name, slug.lower())
    conn.execute(sql, values)


def delete_producer(conn: sqlite3.Connection, slug: str) -> None:
    sql = "DELETE FROM producers WHERE slug = ?"
    values = (slug.lower(), )
    conn.execute(sql, values)


def do_add_producer(conn: sqlite3.Connection, slug: str, name: str) -> None:
    """Add producer to the database."""
    print(f"Adding {slug} to database and setting name={name}")
    insert_producer(conn, slug, name)


def do_list_producers(conn: sqlite3.Connection) -> None:
    """List all producers in the database."""
    for producer in select_producers(conn):
        print(f'{producer["slug"]}: {producer["name"]}')


def do_show_producer(conn: sqlite3.Connection, slug: str) -> None:
    """Show details of one producer in the database."""
    producer = select_producer(conn, slug)
    if producer is not None:
        print(f'{producer["slug"]}: {producer["name"]}')
    else:
        logger.warning("Producer %s not found.", slug)


def do_update_producer(conn: sqlite3.Connection, slug: str) -> None:
    """Input name of producer with slug and update it in the database."""
    producer = select_producer(conn, slug)
    if producer is not None:
        name = input(f"Enter new name for {slug}: ")
        update_producer(conn, slug, name)
    else:
        logger.warning("Producer %s not found.", slug)


def do_delete_producer(conn: sqlite3.Connection, slug: str) -> None:
    """Delete producer <slug> from the database."""
    delete_producer(conn, slug)
