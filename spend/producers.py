import logging
import sqlite3

from .slug import Slug, slug_like_prefix

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


def insert_producer(conn: sqlite3.Connection, slug: Slug, name: str) -> None:
    sql = "INSERT INTO producers (slug, name) VALUES (?, ?)"
    values = (slug, name)
    conn.execute(sql, values)


def select_producers(
    conn: sqlite3.Connection, prefix: str | None = None
) -> list[sqlite3.Row]:
    if prefix:
        sql = "SELECT slug, name FROM producers WHERE slug LIKE ? ESCAPE '\\'"
        res = conn.execute(sql, (slug_like_prefix(prefix),))
    else:
        res = conn.execute("SELECT slug, name FROM producers")
    return res.fetchall()


def select_producer(conn: sqlite3.Connection, slug: Slug) -> sqlite3.Row | None:
    sql = "SELECT producer_id, slug, name FROM producers WHERE slug = ?"
    values = (slug,)
    res = conn.execute(sql, values)
    row: sqlite3.Row | None = res.fetchone()
    return row


def update_producer(conn: sqlite3.Connection, slug: Slug, name: str) -> None:
    sql = "UPDATE producers SET name = ? WHERE slug = ?"
    values = (name, slug)
    conn.execute(sql, values)


def delete_producer(conn: sqlite3.Connection, slug: Slug) -> None:
    sql = "DELETE FROM producers WHERE slug = ?"
    values = (slug,)
    conn.execute(sql, values)


def do_add_producer(conn: sqlite3.Connection, slug: Slug, name: str) -> None:
    """Add producer to the database."""
    insert_producer(conn, slug, name)


def do_list_producers(conn: sqlite3.Connection, prefix: str | None = None) -> None:
    """List producers, optionally only those whose slug starts with `prefix`."""
    for producer in select_producers(conn, prefix):
        print(f"{producer['slug']}: {producer['name']}")


def do_show_producer(conn: sqlite3.Connection, slug: Slug) -> None:
    """Show details of one producer in the database."""
    producer = select_producer(conn, slug)
    if producer is not None:
        print(f"{producer['slug']}: {producer['name']}")
    else:
        logger.warning("Producer %s not found.", slug)


def do_update_producer(conn: sqlite3.Connection, slug: Slug, name: str) -> None:
    """Update producer with slug it in the database."""
    producer = select_producer(conn, slug)
    if producer is not None:
        update_producer(conn, slug, name)
    else:
        logger.warning("Producer %s not found.", slug)


def do_delete_producer(conn: sqlite3.Connection, slug: Slug) -> None:
    """Delete producer <slug> from the database."""
    delete_producer(conn, slug)
