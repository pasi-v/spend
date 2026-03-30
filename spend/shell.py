import cmd
import shlex
from datetime import datetime
from decimal import Decimal, InvalidOperation
import sqlite3
import producers
import products
import stores
import vouchers


commands = {
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
}


def run_tx(conn, fn, *args):
    with conn:
        return fn(conn, *args)

def collect_voucher_lines(conn):
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
            print(e)
            continue
        amount_str = parts[1]
        try:
            amount = Decimal(amount_str)
        except decimal.InvalidOperation:
            print(f"Invalid amount: {amount_str}.  Use '123.45'.")
            continue
        lines.append((product_slug, amount))
    return lines


class SpendShell(cmd.Cmd):
    intro = (
        "Welcome to spend your hard-earned money.  Type help or ? to list commands.\n"
    )
    prompt = "(spend) "

    def __init__(self, conn):
        super().__init__()
        self.conn = conn

    def dispatch(self, entity_name: str, arg: str):
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
            # keep current behavior for add-like commands
            if subcommand == "add" and values:
                print(f'{entity_name.capitalize()} {values[0]} already exists, skipping add.')
            else:
                raise

        
    def do_producer(self, arg):
        """Add, list, show, delete or update producer."""
        self.dispatch("producer", arg)

            
    def do_product(self, arg):
        """Add, list, show, delete or update product."""
        self.dispatch("product", arg)

            
    def do_store(self, arg):
        """Add, list, show, delete or update store."""
        self.dispatch("store", arg)


    def do_voucher(self, arg):
        """Add, list, show, delete or update voucher."""
        tokens = parse(arg)
        if len(tokens) < 1:
            print("usage: voucher [add|list|show|delete|update]")
            return

        subcommand = tokens[0].lower()
        if subcommand not in ("add", "list", "show", "delete", "update"):
            print("usage: voucher [add|list|show|delete|update]")
            return

        if subcommand == "add":
            if len(tokens) < 3:
                print("usage: voucher add <date> <store_slug>")
                return

            date_str = tokens[1]
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print("Invalid date. Use YYYY-MM-DD")
                return
            store_slug = tokens[2]
            try:
                stores.require_store(self.conn, store_slug)
            except ValueError as e:
                print(e)
                return
            lines = collect_voucher_lines(self.conn)
            print(f"Adding voucher date: {d}, store: {store_slug}")
            print(lines)
            run_tx(self.conn, vouchers.do_add_voucher, d, store_slug, lines)
            return
        
        elif subcommand == "list":
            vouchers.do_list_vouchers(self.conn)
            return

        elif subcommand == "show":
            # Vouchers do not have slug, so they have to be shown by database id
            if len(tokens) != 2:
                print("usage: voucher show <id>")
                return
            try:
                id = int(tokens[1])
                vouchers.do_show_voucher(self.conn, id)
            except ValueError:
                print("voucher id must be an integer")
            return

        elif subcommand == "delete":
            # Vouchers do not have slug, so they have to be shown by database id
            if len(tokens) != 2:
                print("usage: voucher delete <id>")
                return
            try:
                id = int(tokens[1])
                run_tx(self.conn, vouchers.do_delete_voucher, id)
            except ValueError:
                print("voucher id must be an integer")
            return

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
