from .db import get_connection, init_db
from .shell import SpendShell


def main():
    conn = get_connection("spend.db")
    with conn:
        init_db(conn)

    SpendShell(conn).cmdloop()
    conn.close()


if __name__ == "__main__":
    main()
