def schema():
    return """
CREATE TABLE IF NOT EXISTS stores (
store_id INTEGER PRIMARY KEY AUTOINCREMENT,
slug TEXT UNIQUE,
name TEXT);

CREATE INDEX IF NOT EXISTS idx_stores_slug 
ON stores(slug);
"""


def insert_store(conn, slug: str, name:str):
    sql = "INSERT INTO stores (slug, name) VALUES (?, ?)"
    values = (slug.lower(), name)
    conn.execute(sql, values)
    conn.commit()


def select_stores(conn):
    sql = "SELECT slug, name FROM stores"
    res = conn.execute(sql)
    return res.fetchall()


def select_store(conn, slug: str):
    sql = "SELECT slug, name FROM stores WHERE slug = ?"
    values = (slug.lower(), )
    res = conn.execute(sql, values)
    return res.fetchone()


def do_add_store(conn, slug: str, name: str):
    """Add store to the database."""
    print(f"Adding {slug} to database and setting name={name}")
    insert_store(conn, slug, name)


def do_list_stores(conn):
    """List all stores in the database."""
    stores = select_stores(conn)
    for store in stores:
        print(f'{store["slug"]}: {store["name"]}')


def do_show_store(conn, slug: str):
    """Show one store identified by slug."""
    store = select_store(conn, slug)
    if store is not None:
        print(f'{store["slug"]}: {store["name"]}')
    else:
        print(f'{store["slug"]} not found.')
