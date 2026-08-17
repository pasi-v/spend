import cmd
import logging
import shlex
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import TypedDict

from . import producers, products, stores, vouchers
from .slug import Slug, to_slug

try:
    import readline
except ImportError:  # pragma: no cover - readline unavailable (e.g. Windows)
    readline = None  # type: ignore[assignment]

DATE_FORMAT = "%Y-%m-%d"

logger = logging.getLogger(__name__)

# Maps an argument name (from a command's "args" spec, "?" stripped) to the
# function that lists existing rows for tab-completion of that argument. Only
# names ending in "_slug" are completable; the same three sources serve every
# command, so `voucher add <date> <store_slug>` completes stores, `product add
# <slug> <name> <producer_slug?>` completes producers, and so on.
CompletionSource = Callable[[sqlite3.Connection], list[sqlite3.Row]]
COMPLETION_SOURCES: dict[str, CompletionSource] = {
    "producer_slug": producers.select_producers,
    "product_slug": products.select_products,
    "store_slug": stores.select_stores,
}


@contextmanager
def slug_completion(slugs: list[str]) -> Iterator[None]:
    """Temporarily install a readline completer over a fixed slug list.

    Used to bring tab-completion to the bare `input()` prompts (voucher lines,
    the producer-slug prompt) that bypass cmd.Cmd's own completion machinery.
    The previous completer is restored on exit; a no-op when readline is
    unavailable.
    """
    if readline is None:
        yield
        return

    def complete(text: str, state: int) -> str | None:
        matches = [s for s in slugs if s.startswith(text)]
        return matches[state] if state < len(matches) else None

    previous = readline.get_completer()
    previous_delims = readline.get_completer_delims()
    readline.set_completer(complete)
    # Break tokens only on whitespace, so a dash in a slug (e.g. "valio-oy")
    # is not treated as a word boundary mid-completion.
    readline.set_completer_delims(" \t\n")
    try:
        yield
    finally:
        readline.set_completer(previous)
        readline.set_completer_delims(previous_delims)


def voucher_add(conn: sqlite3.Connection, date_str: str, store_slug: Slug) -> None:
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


def product_update(conn: sqlite3.Connection,
                   product_slug: Slug,
                   product_name: str) -> None:
    producer_slugs = [row["slug"] for row in producers.select_producers(conn)]
    with slug_completion(producer_slugs):
        raw = input("Enter new producer slug (empty to set null): ").strip()
    producer_slug: Slug | None = to_slug(raw) if raw else None
    products.do_update_product(conn, product_slug, product_name, producer_slug)


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
            "args": ["prefix?"],
            "transaction": False,
        },
        "show": {
            "handler": producers.do_show_producer,
            "args": ["producer_slug"],
            "transaction": False,
        },
        "update": {
            "handler": producers.do_update_producer,
            "args": ["producer_slug", "producer_name"],
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
            "args": ["prefix?"],
            "transaction": False,
        },
        "show": {
            "handler": products.do_show_product,
            "args": ["product_slug"],
            "transaction": False,
        },
        "update": {
            "handler": product_update,
            "args": ["product_slug", "product_name"],
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
            "args": ["prefix?"],
            "transaction": False,
        },
        "show": {
            "handler": stores.do_show_store,
            "args": ["store_slug"],
            "transaction": False,
        },
        "update": {
            "handler": stores.do_update_store,
            "args": ["store_slug", "store_name"],
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
            "handler": voucher_add,  # Note that this is at the UI layer
            "args": ["date", "store_slug"],
            "transaction": True,
        },
        "list": {
            "handler": vouchers.do_list_vouchers,
            "args": [],
            "transaction": False,
        },
        "show": {
            "handler": voucher_show,  # Note that this is at the UI layer
            "args": ["voucher_id"],
            "transaction": False,
        },
        "delete": {
            "handler": voucher_delete,  # Note that this is at the UI layer
            "args": ["voucher_id"],
            "transaction": True,
        },
    },
}


def run_tx(conn: sqlite3.Connection, fn: Callable[..., None], *args: str) -> None:
    with conn:
        fn(conn, *args)


def collect_voucher_lines(conn: sqlite3.Connection) -> list[tuple[Slug, Decimal]]:
    lines = []
    print("Adding voucher lines: <product_slug> <amount in €.cc> (empty line to end)")
    product_slugs = [row["slug"] for row in products.select_products(conn)]
    with slug_completion(product_slugs):
        while True:
            line = input()
            if line == "":
                break
            parts = line.split()
            if len(parts) < 2:
                print("usage: <product_slug> <amount in €.cc>")
                continue
            product_slug = to_slug(parts[0])
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


def _convert_arg(spec: str, value: str) -> str:
    """Args whose spec name ends in '_slug' are normalized via
    to_slug; others pass through unchanged."""
    name = spec.rstrip("?")
    if name.endswith("_slug"):
        return to_slug(value)
    return value


class SpendShell(cmd.Cmd):
    intro = (
        "Welcome to spend your hard-earned money.  Type help or ? to list commands.\n"
    )
    prompt = "(spend) "

    def __init__(self, conn: sqlite3.Connection) -> None:
        super().__init__()
        self.conn = conn

    def preloop(self) -> None:
        # cmd.cmdloop only binds "tab: complete", which libedit (the readline
        # shim on macOS) ignores. Bind the libedit way so Tab completes there
        # too. Harmless when readline is missing.
        if readline is None:
            return
        if "libedit" in (readline.__doc__ or ""):
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")
        # Default delims include "-", which would split a dashed slug
        # ("valio-oy") into two completion tokens. Our commands are
        # whitespace-separated (dispatch uses shlex/split), so break on
        # whitespace only.
        readline.set_completer_delims(" \t\n")

    def _complete(
        self, entity_name: str, text: str, line: str, begidx: int
    ) -> list[str]:
        """Complete a subcommand or a slug argument for an entity command.

        Driven entirely by the `commands` metadata: position 1 completes the
        subcommand; later positions complete against COMPLETION_SOURCES when the
        matching arg name ends in "_slug", and offer nothing otherwise.
        """
        entity_commands = commands[entity_name]
        preceding = line[:begidx].split()  # finished tokens before the cursor
        pos = len(preceding)               # index of the token being completed

        if pos <= 1:  # completing the subcommand itself
            return [s for s in entity_commands if s.startswith(text)]

        sub = entity_commands.get(preceding[1].lower())
        if sub is None:
            return []

        arg_index = pos - 2
        if arg_index >= len(sub["args"]):
            return []

        name = sub["args"][arg_index].rstrip("?")
        source = COMPLETION_SOURCES.get(name)
        if source is None:  # non-slug arg (e.g. a name or date) — no suggestions
            return []

        rows = source(self.conn)
        return [row["slug"] for row in rows if row["slug"].startswith(text)]

    def complete_producer(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        return self._complete("producer", text, line, begidx)

    def complete_product(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        return self._complete("product", text, line, begidx)

    def complete_store(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        return self._complete("store", text, line, begidx)

    def complete_voucher(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        return self._complete("voucher", text, line, begidx)

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

        converted = [_convert_arg(arg_spec[i], values[i]) for i in range(len(values))]

        try:
            if wants_tx:
                run_tx(self.conn, handler, *converted)
            else:
                handler(self.conn, *converted)

        except sqlite3.IntegrityError:
            if subcommand == "add" and converted:
                logger.warning(
                    "%s %s already exists, skipping add.",
                    entity_name.capitalize(),
                    converted[0],
                )
            else:
                logger.error("Database integrity error: %s", entity_name, exc_info=True)
        except sqlite3.OperationalError:
            logger.error(
                "Database error while handling %s %s.",
                entity_name,
                subcommand,
                exc_info=True,
            )
        except sqlite3.ProgrammingError:
            logger.error(
                "Internal error while handling %s %s.",
                entity_name,
                subcommand,
                exc_info=True,
            )

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

    @staticmethod
    def do_EOF(_: str) -> bool:
        """Exit on end-of-file (Ctrl-D)."""
        print()  # move off the prompt line, since Ctrl-D prints no newline
        return True
