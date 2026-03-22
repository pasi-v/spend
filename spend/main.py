from db import Database
from shell import SpendShell


if __name__ == "__main__":
    database = Database("spend.db")
    SpendShell(database).cmdloop()
    database.close()
