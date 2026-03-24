import cmd
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
        print(f'{product["product_slug"]}: {product["product_name"]}, producer: {product["producer_slug"]}')
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


def do_add_store(db: Database, slug: str, name: str):
    """Add store to the database."""
    print(f"Adding {slug} to database and setting name={name}")
    db.insert_store(slug, name)


def do_list_stores(db: Database):
    """List all stores in the database."""
    stores = db.select_stores()
    for store in stores:
        print(f'{store["slug"]}: {store["name"]}')


def do_show_store(db: Database, slug: str):
    """Show one store identified by slug."""
    store = db.select_store(slug)
    if store is not None:
        print(f'{store["slug"]}: {store["name"]}')
    else:
        print(f'{store["slug"]} not found.')


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
            do_add_store(self.db, slug, name)
        elif subcommand == "list":
            do_list_stores(self.db)
        elif subcommand == "show":
            if len(args) != 2:
                print("usage: product show <slug>")
                return
            slug = args[1]
            do_show_store(self.db, slug)

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
