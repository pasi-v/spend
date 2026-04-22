from .producers import *


def schema():
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


def insert_product(conn, product_slug, product_name, producer_id=None):
    sql = "INSERT INTO products (slug, name, producer_id) VALUES (?, ?, ?)"
    values = (product_slug.lower(), product_name, producer_id)
    conn.execute(sql, values)


def select_products(conn):
    sql = "SELECT slug, name FROM products"
    res = conn.execute(sql)
    return res.fetchall()


def select_product(conn, slug):
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
    return res.fetchone()


def update_product(conn, slug: str, name: str, producer_id: int):
    sql = "UPDATE products SET name = ?, producer_id = ? WHERE slug = ?"
    values = (name, producer_id, slug.lower())
    conn.execute(sql, values)


def delete_product(conn, slug):
    sql = "DELETE FROM products WHERE slug = ?"
    values = (slug.lower(), )
    conn.execute(sql, values)


def require_product(conn, slug: str):
    """Return product or raise a ValueError if not found."""
    product = select_product(conn, slug)
    if product is None:
        raise ValueError(f"Unknown product: {slug}")
    return product
    

def do_add_product(conn, product_slug: str, name: str, producer_slug: str=None):
    """Add product <slug> to the database and link to producer if producer_slug provided."""
    print(f"Adding {product_slug} to database and setting name={name}, producer_slug={producer_slug}")
    producer_id = None
    if producer_slug:
        producer = select_producer(conn, producer_slug)
        if producer is not None:
            producer_id = producer["producer_id"]
        else:
            print(f"Producer {producer_slug} not found")
            return

    insert_product(conn, product_slug, name, producer_id)


def do_list_products(conn):
    """List all products in the database."""
    products = select_products(conn)
    for product in products:
        print(f'{product["slug"]}: {product["name"]}')


def do_show_product(conn, slug: str):
    """Show details of one product in the database."""
    product = select_product(conn, slug)
    if product is not None:
        print(f'{product["product_slug"]}: {product["product_name"]}, producer: {product["producer_slug"]}')
    else:
        print(f'Product {slug} not found.')


def do_update_product(conn, slug: str):
    """Input name of product with slug and update it in the database."""
    product = select_product(conn, slug)
    if product is None:
        print(f'Product {slug} not found.')
        return

    producer_id = None
    name = input(f"Enter new name for {slug}: ")
    producer_slug = input(f"Enter new producer slug (empty to set null): ").strip()
    if producer_slug != "":
        producer = select_producer(conn, producer_slug)
        if producer is None:
            print(f"Producer {producer_slug} not found.")
            return
        producer_id = producer["producer_id"]

    update_product(conn, slug, name, producer_id)


def do_delete_product(conn, slug):
    """Delete product <slug> from the database."""
    delete_product(conn, slug)
