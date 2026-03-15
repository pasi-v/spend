import cmd
import sqlite3



def do_add_producer(db, slug, name):
    """Add producer to the database."""
    print(f"Adding {slug} to database and setting name={name}")
    db.insert_producer(slug, name)


class Database():
    def __init__(self, dbname):
        self.con = sqlite3.connect(dbname)
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


    def insert_producer(self, slug, name):
        sql = "INSERT INTO producers (slug, name) VALUES (?, ?)"
        values = (slug.lower(), name)
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
        "Add, list, show, delete or update producer."
        args = arg.split()
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
            else:
                print("not implemented yet")

    def do_quit(self, arg):
        "Stop spending and exit."
        return True

    def do_exit(self, arg):
        "Stop spending and exit."
        return True


if __name__ == "__main__":
    db = Database("spend.db")
    SpendShell(db).cmdloop()
    db.close()
