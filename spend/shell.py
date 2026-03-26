import cmd
import shlex
from datetime import datetime
from decimal import Decimal, InvalidOperation
import producers
import products
import stores
import vouchers


def run_tx(conn, fn, *args):
    with conn:
        return fn(conn, *args)

def collect_voucher_lines(conn):
    lines = []
    print("Adding voucher lines: <product_slug> <amount in €.cc>")
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
                        run_tx(self.conn, producers.do_add_producer, slug, name)
                elif subcommand == "list":
                    producers.do_list_producers(self.conn)
                elif subcommand == "show":
                    if len(args) != 2:
                        print("usage: producer show <slug>")
                    else:
                        slug = args[1]
                        producers.do_show_producer(self.conn, slug)
                elif subcommand == "update":
                    if len(args) != 2:
                        print("usage: producer update <slug>")
                    else:
                        slug = args[1]
                        run_tx(self.conn, producers.do_update_producer, slug)
                elif subcommand == "delete":
                    if len(args) != 2:
                        print("usage: producer delete <slug>")
                    else:
                        slug = args[1]
                        run_tx(self.conn, producers.do_delete_producer, slug)
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
                if len(args) >= 4:
                    producer_slug = args[3]
                run_tx(self.conn, products.do_add_product, product_slug, product_name, producer_slug)
            elif subcommand == "list":
                products.do_list_products(self.conn)
            elif subcommand == "show":
                if len(args) != 2:
                    print("usage: product show <slug>")
                    return
                slug = args[1]
                products.do_show_product(self.conn, slug)

            elif subcommand == "update":
                if len(args) != 2:
                    print("usage: product update <slug>")
                    return
                slug = args[1]
                run_tx(self.conn, products.do_update_product, slug)

            elif subcommand == "delete":
                if len(args) != 2:
                    print("usage: product delete <slug>")
                    return
                slug = args[1]
                run_tx(self.conn, products.do_delete_product, slug)
            else:
                print("not implemented yet")

    def do_store(self, arg):
        """Add, list, show, delete or update store."""
        args = shlex.split(arg)
        if len(args) < 1:
            print("usage: store [add|list|show|delete|update]")
            return

        subcommand = args[0].lower()
        if subcommand not in ("add", "list", "show", "delete", "update"):
            print("usage: store [add|list|show|delete|update]")
            return
        if subcommand == "add":
            if len(args) < 3:
                print("usage: store add <slug> <name>")
                return

            slug = args[1]
            name = args[2]
            run_tx(self.conn, stores.do_add_store, slug, name)
        elif subcommand == "list":
            stores.do_list_stores(self.conn)
        elif subcommand == "show":
            if len(args) != 2:
                print("usage: product show <slug>")
                return
            slug = args[1]
            stores.do_show_store(self.conn, slug)

        elif subcommand == "update":
            if len(args) != 2:
                print("usage: store update <slug>")
                return
            slug = args[1]
            run_tx(self.conn, stores.do_update_store, slug)

        elif subcommand == "delete":
            if len(args) != 2:
                print("usage: store delete <slug>")
                return
            slug = args[1]
            run_tx(self.conn, stores.do_delete_store, slug)

        else:
            print("not implemented yet")


    def do_voucher(self, arg):
        """Add, list, show, delete or update voucher."""
        args = shlex.split(arg)
        if len(args) < 1:
            print("usage: voucher [add|list|show|delete|update]")
            return

        subcommand = args[0].lower()
        if subcommand not in ("add", "list", "show", "delete", "update"):
            print("usage: voucher [add|list|show|delete|update]")
            return

        if subcommand == "add":
            if len(args) < 3:
                print("usage: voucher add <date> <store_slug>>")
                return

            date_str = args[1]
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print("Invalid date. Use YYYY-MM-DD")
                return
            store_slug = args[2]
            try:
                stores.require_store(self.conn, store_slug)
            except ValueError as e:
                print(e)
                return
            lines = collect_voucher_lines(self.conn)
            print(f"Adding voucher date: {d}, store: {store_slug}")
            print(lines)
            run_tx(self.conn, vouchers.do_add_voucher, d, store_slug, lines)

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
