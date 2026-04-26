import logging
import sqlite3

from .producers import select_producer

logger = logging.getLogger(__name__)


def schema() -> str:
    return """
CREATE TABLE IF NOT EXISTS products
(
product_id  INTEGER PRIMARY KEY AUTOINCREMENT,
slug        TEXT UNIQUE,
name        TEXT,
producer_id INTEGER,
FOREIGN KEY(producer_id) REFERENCES producers(producer_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_products_producer
ON products(slug);
"""


def insert_product(conn: sqlite3.Connection,
                   product_slug: str,
                   product_name: str,
                   producer_id: int | None=None) -> None:
    sql = "INSERT INTO products (slug, name, producer_id) VALUES (?, ?, ?)"
    values = (product_slug.lower(), product_name, producer_id)
    conn.execute(sql, values)


def select_products(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    sql = "SELECT slug, name FROM products"
    res = conn.execute(sql)
    return res.fetchall()


def select_product(conn: sqlite3.Connection, slug: str) -> sqlite3.Row | None:
    sql = """
SELECT product_id
 , products.slug AS product_slug
 , products.name AS product_name
 , producers.slug AS producer_slug
 , producers.name AS producer_name
FROM products LEFT JOIN producers ON products.producer_id = producers.producer_id
WHERE products.slug = ?"""
    values = (slug.lower(),)
    res = conn.execute(sql, values)
    row: sqlite3.Row | None = res.fetchone()
    return row


def update_product(conn: sqlite3.Connection, slug: str, name: str, producer_id: int | None) -> None:
    sql = "UPDATE products SET name = ?, producer_id = ? WHERE slug = ?"
    values = (name, producer_id, slug.lower())
    conn.execute(sql, values)


def delete_product(conn: sqlite3.Connection, slug: str) -> None:
    sql = "DELETE FROM products WHERE slug = ?"
    values = (slug.lower(), )
    conn.execute(sql, values)


def require_product(conn: sqlite3.Connection, slug: str) -> sqlite3.Row:
    """Return product or raise a ValueError if not found."""
    product = select_product(conn, slug)
    if product is None:
        raise ValueError(f"Unknown product: {slug}")
    return product


def do_add_product(conn: sqlite3.Connection,
                   product_slug: str,
                   name: str,
                   producer_slug: str | None=None) -> None:
    """Add product <slug> to the database and link to producer if producer_slug provided."""
    print(f"Adding {product_slug} to database and setting name={name}, producer_slug={producer_slug}")
    producer_id = None
    if producer_slug:
        producer = select_producer(conn, producer_slug)
        if producer is not None:
            producer_id = producer["producer_id"]
        else:
            logger.warning("Producer %s not found.", producer_slug)
            return

    insert_product(conn, product_slug, name, producer_id)


def do_list_products(conn: sqlite3.Connection) -> None:
    """List all products in the database."""
    products = select_products(conn)
    for product in products:
        print(f'{product["slug"]}: {product["name"]}')


def do_show_product(conn: sqlite3.Connection, slug: str) -> None:
    """Show details of one product in the database."""
    product = select_product(conn, slug)
    if product is not None:
        print(f'{product["product_slug"]}: {product["product_name"]}, producer: {product["producer_slug"]}')
    else:
        logger.warning("Product %s not found.", slug)


def do_update_product(conn: sqlite3.Connection, slug: str) -> None:
    """Input name of product with slug and update it in the database."""
    product = select_product(conn, slug)
    if product is None:
        logger.warning("Product %s not found.", slug)
        return

    producer_id = None
    name = input(f"Enter new name for {slug}: ")
    producer_slug = input("Enter new producer slug (empty to set null): ").strip()
    if producer_slug != "":
        producer = select_producer(conn, producer_slug)
        if producer is None:
            logger.warning("Producer %s not found.", producer_slug)
            return
        producer_id = producer["producer_id"]

    update_product(conn, slug, name, producer_id)


def do_delete_product(conn: sqlite3.Connection, slug: str) -> None:
    """Delete product <slug> from the database."""
    delete_product(conn, slug)
