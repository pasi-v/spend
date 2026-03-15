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


class Database:
    def __init__(self, dbname):
        self.con = sqlite3.connect(dbname)
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()
        self.ensure_producers()

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
        sql = "SELECT slug, name FROM producers WHERE slug = ?"
        values = (slug, )
        res = self.con.execute(sql, values)
        return res.fetchone()
    

    def update_producer(self, slug, name):
        sql = "UPDATE producers SET name = ? WHERE slug = ?"
        values = (name, slug)
        self.con.execute(sql, values)
        self.con.commit()


    def delete_producer(self, slug):
        sql = "DELETE FROM producers WHERE slug = ?"
        values = (slug, )
        self.con.execute(sql, values)
        self.con.commit()


    def close(self):
        self.con.close()


class SpendShell(cmd.Cmd):
    intro = (
        "Welcome to spend your hard-earned money.  Type help or ? to list commands.\n"
    )
    prompt = "(spend) "

    def __init__(self, db):
        super().__init__()
        self.db = db

    def do_producer(self, arg):
        """Add, list, show, delete or update producer."""
        args = shlex.split(arg)
        if len(args) < 1:
            print("usage: producer [add|list|show|delete|update]")
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
