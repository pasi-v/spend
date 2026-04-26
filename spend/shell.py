import cmd
import logging
import shlex
import sqlite3
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import TypedDict

from . import producers, products, stores, vouchers

DATE_FORMAT = "%Y-%m-%d"

logger = logging.getLogger(__name__)


def voucher_add(conn: sqlite3.Connection, date_str: str, store_slug: str) -> None:
    # 1. Parse date
    try:
        d = datetime.strptime(date_str, DATE_FORMAT).date()
    except ValueError:
        logger.error("Invalid date. Use YYYY-MM-DD")
        return

    # 2. Validate store
    try:
        stores.require_store(conn, store_slug)
    except ValueError as e:
        logger.error("%s", e)
        return

    # 3. Collect voucher lines (interactive)
    lines = collect_voucher_lines(conn)

    # 4. Final action
    logger.debug("Adding voucher date: %s, store: %s", d, store_slug)
    logger.debug("Lines: %s", lines)

    vouchers.do_add_voucher(conn, d, store_slug, lines)


def voucher_show(conn: sqlite3.Connection, id_str: str) -> None:
    # Vouchers do not have slug, so they have to be shown by database id
    try:
        id = int(id_str)
        vouchers.do_show_voucher(conn, id)
    except ValueError:
        logger.error("voucher id must be an integer")
    return


def voucher_delete(conn: sqlite3.Connection, id_str: str) -> None:
    # Vouchers do not have slug, so they have to be deleted by database id
    try:
        id = int(id_str)
        vouchers.do_delete_voucher(conn, id)
    except ValueError:
        logger.error("voucher id must be an integer")
    return


class CommandSpec(TypedDict):
    handler: Callable[..., None]
    args: list[str]
    transaction: bool


commands: dict[str, dict[str, CommandSpec]] = {
    "producer": {
        "add": {
            "handler": producers.do_add_producer,
            "args": ["producer_slug", "producer_name"],
            "transaction": True,
        },
        "list": {
            "handler": producers.do_list_producers,
            "args": [],
            "transaction": False,
        },
        "show": {
            "handler": producers.do_show_producer,
            "args": ["producer_slug"],
            "transaction": False,
        },
        "update": {
            "handler": producers.do_update_producer,
            "args": ["producer_slug"],
            "transaction": True,
        },
        "delete": {
            "handler": producers.do_delete_producer,
            "args": ["producer_slug"],
            "transaction": True,
        },
    },
    "product": {
        "add": {
            "handler": products.do_add_product,
            "args": ["product_slug", "product_name", "producer_slug?"],
            "transaction": True,
        },
        "list": {
            "handler": products.do_list_products,
            "args": [],
            "transaction": False,
        },
        "show": {
            "handler": products.do_show_product,
            "args": ["product_slug"],
            "transaction": False,
        },
        "update": {
            "handler": products.do_update_product,
            "args": ["product_slug"],
            "transaction": True,
        },
        "delete": {
            "handler": products.do_delete_product,
            "args": ["product_slug"],
            "transaction": True,
        },
    },
    "store": {
        "add": {
            "handler": stores.do_add_store,
            "args": ["store_slug", "store_name"],
            "transaction": True,
        },
        "list": {
            "handler": stores.do_list_stores,
            "args": [],
            "transaction": False,
        },
        "show": {
            "handler": stores.do_show_store,
            "args": ["store_slug"],
            "transaction": False,
        },
        "update": {
            "handler": stores.do_update_store,
            "args": ["store_slug"],
            "transaction": True,
        },
        "delete": {
            "handler": stores.do_delete_store,
            "args": ["store_slug"],
            "transaction": True,
        },
    },
    "voucher": {
        "add": {
            "handler": voucher_add,    # Note that this is at the UI layer
            "args": ["date", "store_slug"],
            "transaction": True,
        },
        "list": {
            "handler": vouchers.do_list_vouchers,
            "args": [],
            "transaction": False,
        },
        "show": {
            "handler": voucher_show,   # Note that this is at the UI layer
            "args": ["voucher_id"],
            "transaction": False,
        },
        "delete": {
            "handler": voucher_delete, # Note that this is at the UI layer
            "args": ["voucher_id"],
            "transaction": True,
        },
    },
}


def run_tx(conn: sqlite3.Connection, fn: Callable[..., None], *args: str) -> None:
    with conn:
        fn(conn, *args)

def collect_voucher_lines(conn: sqlite3.Connection) -> list[tuple[str, Decimal]]:
    lines = []
    print("Adding voucher lines: <product_slug> <amount in €.cc> (empty line to end)")
    while True:
        line = input()
        if line == "":
            break
        parts = line.split()
        if len(parts) < 2:
            print("usage: <product_slug> <amount in €.cc>")
            continue
        product_slug = parts[0]
        try:
            products.require_product(conn, product_slug)
        except ValueError as e:
            logger.error("%s", e)
            continue
        amount_str = parts[1]
        try:
            amount = Decimal(amount_str)
        except InvalidOperation:
            logger.error("Invalid amount: %s.  Use '123.45'.", amount_str)
            continue
        lines.append((product_slug, amount))
    return lines


class SpendShell(cmd.Cmd):
    intro = (
        "Welcome to spend your hard-earned money.  Type help or ? to list commands.\n"
    )
    prompt = "(spend) "

    def __init__(self, conn: sqlite3.Connection) -> None:
        super().__init__()
        self.conn = conn

    def dispatch(self, entity_name: str, arg: str) -> None:
        args = shlex.split(arg)
        entity_commands = commands[entity_name]

        if not args:
            subs = "|".join(entity_commands.keys())
            print(f"usage: {entity_name} [{subs}]")
            return

        subcommand = args[0].lower()
        sub = entity_commands.get(subcommand)

        if sub is None:
            subs = "|".join(entity_commands.keys())
            print(f"usage: {entity_name} [{subs}]")
            return

        handler = sub["handler"]
        arg_spec = sub["args"]
        wants_tx = sub["transaction"]

        values = args[1:]

        required = [a for a in arg_spec if not a.endswith("?")]
        optional = [a for a in arg_spec if a.endswith("?")]

        if not (len(required) <= len(values) <= len(required) + len(optional)):
            usage = " ".join(arg_spec)
            print(f"usage: {entity_name} {subcommand} {usage}")
            return

        try:
            if wants_tx:
                run_tx(self.conn, handler, *values)
            else:
                handler(self.conn, *values)

        except sqlite3.IntegrityError:
            if subcommand == "add" and values:
                logger.warning("%s %s already exists, skipping add.", entity_name.capitalize(), values[0])
            else:
                logger.error("Database integrity error: %s", entity_name, exc_info=True)
        except sqlite3.OperationalError:
            logger.error("Database error while handling %s %s.", entity_name, subcommand, exc_info=True)
        except sqlite3.ProgrammingError:
            logger.error("Internal error while handling %s %s.", entity_name, subcommand, exc_info=True)


    def do_producer(self, arg: str) -> None:
        """Add, list, show, delete or update producer."""
        self.dispatch("producer", arg)


    def do_product(self, arg: str) -> None:
        """Add, list, show, delete or update product."""
        self.dispatch("product", arg)


    def do_store(self, arg: str) -> None:
        """Add, list, show, delete or update store."""
        self.dispatch("store", arg)


    def do_voucher(self, arg: str) -> None:
        """Add, list, show, delete or update voucher."""
        self.dispatch("voucher", arg)

    @staticmethod
    def do_quit(_: str) -> bool:
        """Stop spending and exit."""
        return True

    @staticmethod
    def do_exit(_: str) -> bool:
        """Stop spending and exit."""
        return True
