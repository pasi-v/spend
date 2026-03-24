import cmd
import shlex
import producers
import products
import stores


def run_tx(conn, fn, *args):
    with conn:
        return fn(conn, *args)


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
                if len(args) >= 3:
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
