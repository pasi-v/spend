def schema():
    sql = """
CREATE TABLE IF NOT EXISTS voucher (
    voucher_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    product_id INTEGER REFERENCES products(product_id) ON DELETE RESTRICT,
    store_id INTEGER REFERENCES stores(store_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_product_id
ON voucher(product_id);

CREATE INDEX IF NOT EXISTS idx_store_id
ON voucher(store_id);
"""
    return sql