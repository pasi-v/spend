from datetime import date
import stores
import products


def schema():
    sql = """
CREATE TABLE IF NOT EXISTS vouchers (
    voucher_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL
    CHECK (
        date LIKE '____-__-__'
        AND date(date) IS NOT NULL
    ),
    amount_cents INTEGER NOT NULL,
    product_id INTEGER REFERENCES products(product_id) ON DELETE RESTRICT,
    store_id INTEGER REFERENCES stores(store_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_vouchers_product
ON vouchers(product_id);

CREATE INDEX IF NOT EXISTS idx_vouchers_store
ON vouchers(store_id);
"""
    return sql


def insert_voucher_line(conn, product_id: int, amount_cents: int, d: date, store_id: int):
    sql = "INSERT INTO vouchers (date, amount_cents, product_id, store_id) VALUES (?, ?, ?, ?)"
    values = (d.isoformat(), amount_cents, product_id, store_id)
    conn.execute(sql, values)


def do_add_voucher(conn, d: date, store_slug: str, lines: list):
    store = stores.require_store(conn, store_slug)
    if store is None:
        raise ValueError(f"Unknown store: {store_slug}")

    for line in lines:
        product_slug = line[0]
        amount_decimal = line[1]
        product_id = products.require_product(conn, product_slug)["product_id"]
        amount_cents = int(amount_decimal * 100)
        insert_voucher_line(conn, product_id, amount_cents, d, store["store_id"])


def select_vouchers(conn):
    sql = """SELECT v.voucher_id, v.date, v.amount_cents, p.slug AS product_slug, s.slug AS store_slug
    FROM vouchers as v
    LEFT JOIN products as p ON v.product_id = p.product_id
    LEFT JOIN stores as s ON v.store_id = s.store_id"""

    res = conn.execute(sql)
    return res.fetchall()

    
def do_list_vouchers(conn):
    res = select_vouchers(conn)
    for v in res:
        print(f"{v['voucher_id']} {v['date']} {v['amount_cents']/100} {v['product_slug']} {v['store_slug']}")


def select_voucher(conn, voucher_id: int):
    sql = """SELECT v.voucher_id, v.date, v.amount_cents, p.slug AS product_slug, s.slug AS store_slug
    FROM vouchers as v
    LEFT JOIN products as p ON v.product_id = p.product_id
    LEFT JOIN stores as s ON v.store_id = s.store_id
    WHERE voucher_id = ?"""

    values = (voucher_id, )
    res = conn.execute(sql, values)
    return res.fetchone()


def do_show_voucher(conn, voucher_id: int):
    """Show a single voucher identified by voucher_id."""
    v = select_voucher(conn, voucher_id)
    if v is None:
        print(f"Could not find voucher {voucher_id}")
        return
    print(f"{v['voucher_id']} {v['date']} {v['amount_cents']/100} {v['product_slug']} {v['store_slug']}")


def delete_voucher(conn, voucher_id: int):
    sql = "DELETE FROM vouchers WHERE voucher_id = ?"
    values = (voucher_id, )
    conn.execute(sql, values)


def do_delete_voucher(conn, voucher_id: int):
    """Delete voucher with id from the database."""
    delete_voucher(conn, voucher_id)
