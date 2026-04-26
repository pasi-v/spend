import argparse
import logging

from .db import get_connection, init_db
from .shell import SpendShell


def main() -> None:
    parser = argparse.ArgumentParser(description="Personal spending tracker")
    parser.add_argument("--verbose", action="store_true", help="Enable debug output")
    parser.add_argument("--db", "-d",
                        default="spend.db",
                        help="Path to SQLite database file (default: spend.db)")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(format="%(levelname)s: %(message)s", level=level)

    conn = get_connection(args.db)
    with conn:
        init_db(conn)

    SpendShell(conn).cmdloop()
    conn.close()


if __name__ == "__main__":
    main()
