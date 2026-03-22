import cmd
import sqlite3
import shlex


def do_add_producer(db, slug, name):
    """Add producer to the database."""
    print(f"Adding {slug} to database and setting name={name}")
    db.insert_producer(slug, name)


def do_list_producers(db):
    """List all producers in the database."""
    producers = db.select_producers()
    for producer in producers:
        print(f'{producer["slug"]}: {producer["name"]}')


def do_show_producer(db, slug):
    """Show details of one producer in the database."""
    producer = db.select_producer(slug)
    if producer is not None:
        print(f'{producer["slug"]}: {producer["name"]}')
    else:
        print(f'Producer {slug} not found.')


def do_update_producer(db, slug):
    """Input name of producer with slug and update it in the database."""
    producer = db.select_producer(slug)
    if producer is not None:
        name = input(f"Enter new name for {slug}: ")
        db.update_producer(slug, name)
    else:
        print(f'Producer {slug} not found.')


def do_delete_producer(db, slug):
    """Delete producer <slug> from the database."""
    db.delete_producer(slug)


def do_add_product(db: Database, product_slug: str, name: str, producer_slug: str=None):
    """Add product <slug> to the database and link to producer if producer_slug provided."""
    print(f"Adding {product_slug} to database and setting name={name}, producer_slug={producer_slug}")
    producer_id = None
    if producer_slug:
        producer = db.select_producer(producer_slug)
        if producer is not None:
            producer_id = producer["producer_id"]
        else:
            print(f"Producer {producer_slug} not found")
            return

    db.insert_product(product_slug, name, producer_id)


def do_list_products(db: Database):
    """List all products in the database."""
    products = db.select_products()
    for product in products:
        print(f'{product["slug"]}: {product["name"]}')


def do_show_product(db: Database, slug: str):
    """Show details of one product in the database."""
    product = db.select_product(slug)
    if product is not None:
        print(f'{product["slug"]}: {product["name"]}')
    else:
        print(f'Product {slug} not found.')


def do_update_product(db: Database, slug: str):
    """Input name of product with slug and update it in the database."""
    product = db.select_product(slug)
    if product is None:
        print(f'Product {slug} not found.')
        return

    producer_id = None
    name = input(f"Enter new name for {slug}: ")
    producer_slug = input(f"Enter new producer slug (empty to set null): ").strip()
    if producer_slug != "":
        producer = db.select_producer(producer_slug)
        if producer is None:
            print(f"Producer {producer_slug} not found.")
            return
        producer_id = producer["producer_id"]

    db.update_product(slug, name, producer_id)


def do_delete_product(db: Database, slug):
    """Delete product <slug> from the database."""
    db.delete_product(slug)


class Database:
    def __init__(self, dbname):
        self.con = sqlite3.connect(dbname)
        self.con.execute("PRAGMA foreign_keys = 1")
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()
        self.ensure_producers()
        self.ensure_products()


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
        sql = "SELECT product_id, slug, name FROM products WHERE slug = ?"
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


    def close(self):
        self.con.close()


class SpendShell(cmd.Cmd):
    intro = (
        "Welcome to spend your hard-earned money.  Type help or ? to list commands.\n"
    )
    prompt = "(spend) "

    def __init__(self, db: Database):
        super().__init__()
        self.db = db

    def do_producer(self, arg):
        """Add, list, show, delete or update producer."""
        args = shlex.split(arg)
        if len(args) < 1:
            print("usage: producer [add|list|show|delete|update]")
            return
        else:
            subcommand = args[0].lower()
            if subcommand not in ("add", "list", "show", "delete", "update"):
                print("usage: producer [add|list|show|delete|update]")
            else:
                if subcommand == "add":
                    if len(args) != 3:
                        print("usage: producer add <slug> <name>")
                    else:
                        slug = args[1]
                        name = args[2]
                        do_add_producer(self.db, slug, name)
                elif subcommand == "list":
                    do_list_producers(self.db)
                elif subcommand == "show":
                    if len(args) != 2:
                        print("usage: producer show <slug>")
                    else:
                        slug = args[1]
                        do_show_producer(self.db, slug)
                elif subcommand == "update":
                    if len(args) != 2:
                        print("usage: producer update <slug>")
                    else:
                        slug = args[1]
                        do_update_producer(self.db, slug)
                elif subcommand == "delete":
                    if len(args) != 2:
                        print("usage: producer delete <slug>")
                    else:
                        slug = args[1]
                        do_delete_producer(self.db, slug)
                else:
                    print("not implemented yet")

    def do_product(self, arg):
        """Add, list, show, delete or update product."""
        args = shlex.split(arg)
        if len(args) < 1:
            print("usage: product [add|list|show|delete|update]")
            return
        else:
            subcommand = args[0].lower()
            if subcommand not in ("add", "list", "show", "delete", "update"):
                print("usage: product [add|list|show|delete|update]")
                return

            if subcommand == "add":
                if len(args) < 3:
                    print("usage: product add <slug> <name> <producer_slug>")
                    return

                product_slug = args[1]
                product_name = args[2]
                producer_slug = None
                if len(args) >= 3:
                    producer_slug = args[3]
                do_add_product(self.db, product_slug, product_name, producer_slug)
            elif subcommand == "list":
                do_list_products(self.db)
            elif subcommand == "show":
                if len(args) != 2:
                    print("usage: product show <slug>")
                    return
                slug = args[1]
                do_show_product(self.db, slug)

            elif subcommand == "update":
                if len(args) != 2:
                    print("usage: product update <slug>")
                    return
                slug = args[1]
                do_update_product(self.db, slug)

            elif subcommand == "delete":
                if len(args) != 2:
                    print("usage: product delete <slug>")
                    return
                slug = args[1]
                do_delete_product(self.db, slug)
            else:
                print("not implemented yet")

    @staticmethod
    def do_quit(_):
        """Stop spending and exit."""
        return True

    @staticmethod
    def do_exit(_):
        """Stop spending and exit."""
        return True


if __name__ == "__main__":
    database = Database("spend.db")
    SpendShell(database).cmdloop()
    database.close()
