import sqlite3

class Database:
    def __init__(self, dbname):
        self.con = sqlite3.connect(dbname)
        self.con.execute("PRAGMA foreign_keys = 1")
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()
        self.ensure_producers()
        self.ensure_products()
        self.ensure_stores()


    def ensure_producers(self):
        sql = """
CREATE TABLE IF NOT EXISTS producers (
producer_id INTEGER PRIMARY KEY AUTOINCREMENT,
slug TEXT UNIQUE,
name TEXT
)"""

        self.cur.execute(sql)
        sql = """
CREATE INDEX IF NOT EXISTS idx_producers_slug 
ON producers(slug)"""
        self.cur.execute(sql)


    def insert_producer(self, slug, name):
        sql = "INSERT INTO producers (slug, name) VALUES (?, ?)"
        values = (slug.lower(), name)
        self.con.execute(sql, values)
        self.con.commit()


    def select_producers(self):
        sql = "SELECT slug, name FROM producers"
        res = self.con.execute(sql)
        return res.fetchall()
    

    def select_producer(self, slug):
        sql = "SELECT producer_id, slug, name FROM producers WHERE slug = ?"
        values = (slug.lower(), )
        res = self.con.execute(sql, values)
        return res.fetchone()
    

    def update_producer(self, slug, name):
        sql = "UPDATE producers SET name = ? WHERE slug = ?"
        values = (name, slug.lower())
        self.con.execute(sql, values)
        self.con.commit()


    def delete_producer(self, slug):
        sql = "DELETE FROM producers WHERE slug = ?"
        values = (slug.lower(), )
        self.con.execute(sql, values)
        self.con.commit()


    def ensure_products(self):
        sql = """
CREATE TABLE IF NOT EXISTS products
(
    product_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT UNIQUE,
    name        TEXT,
    producer_id INTEGER,
    FOREIGN KEY(producer_id) REFERENCES producers(producer_id) ON DELETE RESTRICT
)"""
        self.cur.execute(sql)
        sql = """
CREATE INDEX IF NOT EXISTS idx_products_slug 
ON products(slug)"""
        self.cur.execute(sql)


    def insert_product(self, product_slug, product_name, producer_id=None):
        sql = "INSERT INTO products (slug, name, producer_id) VALUES (?, ?, ?)"
        values = (product_slug.lower(), product_name, producer_id)
        self.con.execute(sql, values)
        self.con.commit()


    def select_products(self):
        sql = "SELECT slug, name FROM products"
        res = self.con.execute(sql)
        return res.fetchall()


    def select_product(self, slug):
        sql = """
SELECT product_id
     , products.slug AS product_slug
     , products.name AS product_name
     , producers.slug AS producer_slug
     , producers.name AS producer_name
FROM products LEFT JOIN producers ON products.producer_id = producers.producer_id
WHERE products.slug = ?"""
        values = (slug.lower(),)
        res = self.con.execute(sql, values)
        return res.fetchone()


    def update_product(self, slug: str, name: str, producer_id: int):
        sql = "UPDATE products SET name = ?, producer_id = ? WHERE slug = ?"
        values = (name, producer_id, slug.lower())
        self.con.execute(sql, values)
        self.con.commit()


    def delete_product(self, slug):
        sql = "DELETE FROM products WHERE slug = ?"
        values = (slug.lower(), )
        self.con.execute(sql, values)
        self.con.commit()


    def ensure_stores(self):
        sql = """
CREATE TABLE IF NOT EXISTS stores (
store_id INTEGER PRIMARY KEY AUTOINCREMENT,
slug TEXT UNIQUE,
name TEXT
)"""

        self.cur.execute(sql)
        sql = """
CREATE INDEX IF NOT EXISTS idx_stores_slug 
ON stores(slug)"""
        self.cur.execute(sql)


    def insert_store(self, slug: str, name:str):
        sql = "INSERT INTO stores (slug, name) VALUES (?, ?)"
        values = (slug.lower(), name)
        self.con.execute(sql, values)
        self.con.commit()


    def select_stores(self):
        sql = "SELECT slug, name FROM stores"
        res = self.con.execute(sql)
        return res.fetchall()


    def select_store(self, slug: str):
        sql = "SELECT slug, name FROM stores WHERE slug = ?"
        values = (slug.lower(), )
        res = self.con.execute(sql, values)
        return res.fetchone()


    def close(self):
        self.con.close()

