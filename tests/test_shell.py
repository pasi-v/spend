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
from spend.shell import SpendShell
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
