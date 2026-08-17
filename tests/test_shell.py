"""Tests for SpendShell, the cmd.Cmd subclass that drives the CLI.

Notes for extending this file:

- `onecmd(line)` is the public cmd.Cmd entry point: parses the line, routes
  to `do_<entity>`, which calls `dispatch`. Tests here drive `onecmd` rather
  than `dispatch` directly so the full input chain is exercised.

- Quoting follows shlex rules: `onecmd("producer add ACME 'Acme Corp'")`
  works because `dispatch` runs `shlex.split` on the arg string.

- Subcommands marked `transaction: True` in the dispatch table commit via
  `with conn:`. The test sees committed state on the same connection — no
  extra setup or commit needed.

- `dispatch` swallows `sqlite3.IntegrityError`, `OperationalError`, and
  `ProgrammingError` and logs them. Don't assert on raised exceptions for
  those paths — use pytest's `caplog` to assert on log records instead.

- `do_quit` / `do_exit` return True; `onecmd` returns that value to signal
  the cmd loop to stop. Calling them from a test does not raise.
"""

import sqlite3

import pytest

from spend.producers import select_producer
from spend.products import select_product
from spend.shell import SpendShell, slug_completion
from spend.slug import to_slug


@pytest.fixture
def shell(conn: sqlite3.Connection) -> SpendShell:
    """SpendShell wired to the in-memory DB from conftest.py's `conn` fixture."""
    return SpendShell(conn)


def test_dispatch_normalizes_slug(shell, conn):
    """Regression test for the slug-normalization bug.

    Every data-layer test passes already-normalized slugs via to_slug(),
    so a regression in shell._convert_arg would not fail any of them.
    Driving the full cmd.Cmd → do_producer → dispatch chain with raw
    uppercase input is what catches it.
    """
    shell.onecmd("producer add ACME 'Acme Corp'")

    row = select_producer(conn, to_slug("acme"))
    assert row is not None
    assert row["slug"] == "acme"
    assert row["name"] == "Acme Corp"


def test_list_captures_stdout(shell, capsys):
    """For tests asserting on printed output, use pytest's `capsys` fixture."""
    shell.onecmd("producer add acme 'Acme Corp'")
    capsys.readouterr()  # discard the "Adding acme..." line from `add`

    shell.onecmd("producer list")

    out = capsys.readouterr().out
    assert "acme: Acme Corp" in out


def test_list_with_prefix_filters(shell, capsys):
    """`<entity> list <prefix>` lists only slugs starting with the prefix."""
    shell.onecmd("producer add valio 'Valio'")
    shell.onecmd("producer add vaasan 'Vaasan'")
    shell.onecmd("producer add atria 'Atria'")
    capsys.readouterr()

    shell.onecmd("producer list va")

    out = capsys.readouterr().out
    assert "valio" in out
    assert "vaasan" in out
    assert "atria" not in out


def test_list_prefix_is_case_insensitive(shell, capsys):
    """The prefix is normalized, so uppercase input matches lowercased slugs."""
    shell.onecmd("store add lidl 'Lidl'")
    shell.onecmd("store add prisma 'Prisma'")
    capsys.readouterr()

    shell.onecmd("store list L")

    out = capsys.readouterr().out
    assert "lidl" in out
    assert "prisma" not in out


def test_list_without_prefix_still_lists_all(shell, capsys):
    """Omitting the optional prefix keeps the original list-everything behavior."""
    shell.onecmd("product add milk 'Milk'")
    shell.onecmd("product add bread 'Bread'")
    capsys.readouterr()

    shell.onecmd("product list")

    out = capsys.readouterr().out
    assert "milk" in out
    assert "bread" in out


def test_update_producer_changes_name(shell, conn):
    shell.onecmd("producer add acme 'Acme Corp'")

    shell.onecmd("producer update acme 'Acme Inc'")

    row = select_producer(conn, to_slug("acme"))
    assert row is not None
    assert row["name"] == "Acme Inc"


def test_update_product_prompts_for_producer(shell, conn, monkeypatch):
    """`product update` takes the new name as an arg and prompts for producer slug."""
    shell.onecmd("producer add acme 'Acme Corp'")
    shell.onecmd("producer add globex 'Globex'")
    shell.onecmd("product add bread 'Bread' acme")
    monkeypatch.setattr("builtins.input", lambda *_: "globex")

    shell.onecmd("product update bread 'Sourdough'")

    row = select_product(conn, to_slug("bread"))
    assert row is not None
    assert row["product_name"] == "Sourdough"
    assert row["producer_slug"] == "globex"


# ---------------------------------------------------------------------------
# Tab-completion
#
# The `complete_<entity>` methods are pure functions of (text, line, begidx),
# so they can be driven directly without a terminal. `begidx` is where the
# token being completed starts in `line`; for a trailing token we pass
# `len(line)`. `endidx` is unused by our completer, so any value works.
# ---------------------------------------------------------------------------


def test_complete_subcommand_lists_all(shell):
    line = "producer "
    result = shell.complete_producer("", line, len(line), len(line))
    assert set(result) == {"add", "list", "show", "update", "delete"}


def test_complete_subcommand_by_prefix(shell):
    line = "producer l"
    result = shell.complete_producer("l", line, len(line) - 1, len(line))
    assert result == ["list"]


def test_complete_slug_arg_lists_existing(shell):
    shell.onecmd("producer add acme 'Acme Corp'")
    shell.onecmd("producer add globex 'Globex'")

    line = "producer show "
    result = shell.complete_producer("", line, len(line), len(line))

    assert set(result) == {"acme", "globex"}


def test_complete_slug_arg_by_prefix(shell):
    shell.onecmd("producer add acme 'Acme Corp'")
    shell.onecmd("producer add globex 'Globex'")

    line = "producer show gl"
    result = shell.complete_producer("gl", line, len(line) - 2, len(line))

    assert result == ["globex"]


def test_complete_crosses_entity_boundary_for_store_slug(shell):
    """`voucher add <date> <store_slug>` completes stores, not vouchers."""
    shell.onecmd("store add lidl 'Lidl'")
    shell.onecmd("store add prisma 'Prisma'")

    line = "voucher add 2026-01-01 "
    result = shell.complete_voucher("", line, len(line), len(line))

    assert set(result) == {"lidl", "prisma"}


def test_complete_optional_producer_slug_on_product_add(shell):
    """The trailing optional `producer_slug?` arg completes producers."""
    shell.onecmd("producer add acme 'Acme Corp'")

    line = "product add bread Bread "
    result = shell.complete_product("", line, len(line), len(line))

    assert result == ["acme"]


def test_complete_slug_containing_dash(shell):
    """Regression: dashed slugs must complete as a single token.

    Readline's default delimiters include "-", which would split "valio-"
    mid-completion. preloop() / slug_completion narrow the delimiters to
    whitespace; here we drive _complete with the begidx readline reports
    under whitespace-only delimiters (the token starts after "show ").
    """
    shell.onecmd("producer add valio-oy 'Valio Oy'")
    shell.onecmd("producer add valio-aura 'Valio Aura'")
    shell.onecmd("producer add atria 'Atria'")

    line = "producer show valio-"
    begidx = len("producer show ")
    result = shell.complete_producer("valio-", line, begidx, len(line))

    assert set(result) == {"valio-oy", "valio-aura"}


def test_preloop_excludes_dash_from_delimiters(shell):
    readline = pytest.importorskip("readline")
    shell.preloop()
    assert "-" not in readline.get_completer_delims()


def test_slug_completion_narrows_and_restores_delimiters(shell):
    readline = pytest.importorskip("readline")
    readline.set_completer_delims(" \t\n-")  # a delim set that includes "-"
    before = readline.get_completer_delims()

    with slug_completion(["valio-oy"]):
        assert "-" not in readline.get_completer_delims()
    assert readline.get_completer_delims() == before


def test_complete_offers_nothing_for_name_argument(shell):
    """A non-slug arg (the product name) has no completion source."""
    line = "product add bread "
    result = shell.complete_product("", line, len(line), len(line))

    assert result == []


def test_complete_unknown_subcommand_offers_nothing(shell):
    line = "producer bogus "
    result = shell.complete_producer("", line, len(line), len(line))

    assert result == []


def test_slug_completion_context_installs_and_restores(shell):
    readline = pytest.importorskip("readline")

    before = readline.get_completer()
    with slug_completion(["acme", "globex", "gloria"]):
        completer = readline.get_completer()
        assert completer is not None
        assert completer("ac", 0) == "acme"
        assert completer("ac", 1) is None
        assert completer("gl", 0) == "globex"
        assert completer("gl", 1) == "gloria"
        assert completer("gl", 2) is None
    assert readline.get_completer() is before


def test_voucher_lines_prompt_completes_products(shell, monkeypatch):
    """The interactive voucher-line loop offers product slugs at its prompt."""
    readline = pytest.importorskip("readline")
    shell.onecmd("store add lidl 'Lidl'")
    shell.onecmd("product add milk 'Milk'")
    shell.onecmd("product add muesli 'Muesli'")

    captured = {}

    def fake_input(*_):
        completer = readline.get_completer()
        captured["matches"] = [completer("m", i) for i in range(3)]
        return ""  # end the voucher-line loop immediately

    monkeypatch.setattr("builtins.input", fake_input)
    shell.onecmd("voucher add 2026-01-01 lidl")

    assert set(captured["matches"]) == {"milk", "muesli", None}


def test_product_update_prompt_completes_producers(shell, conn, monkeypatch):
    """The producer-slug prompt in `product update` offers producer slugs."""
    readline = pytest.importorskip("readline")
    shell.onecmd("producer add acme 'Acme Corp'")
    shell.onecmd("product add bread 'Bread' acme")

    captured = {}

    def fake_input(*_):
        completer = readline.get_completer()
        captured["match"] = completer("ac", 0)
        return "acme"

    monkeypatch.setattr("builtins.input", fake_input)
    shell.onecmd("product update bread 'Sourdough'")

    assert captured["match"] == "acme"
