from spend.producers import (
    delete_producer,
    insert_producer,
    select_producer,
    select_producers,
    update_producer,
)
from spend.slug import to_slug


def test_insert_and_select_all(conn):
    insert_producer(conn, to_slug("acme"), "Acme Corp")
    rows = select_producers(conn)
    assert len(rows) == 1
    assert rows[0]["slug"] == "acme"
    assert rows[0]["name"] == "Acme Corp"


def test_select_producers_filters_by_prefix(conn):
    insert_producer(conn, to_slug("valio"), "Valio")
    insert_producer(conn, to_slug("vaasan"), "Vaasan")
    insert_producer(conn, to_slug("atria"), "Atria")

    rows = select_producers(conn, "va")

    assert {r["slug"] for r in rows} == {"valio", "vaasan"}


def test_select_producers_prefix_is_case_insensitive(conn):
    insert_producer(conn, to_slug("valio"), "Valio")

    rows = select_producers(conn, "VA")

    assert {r["slug"] for r in rows} == {"valio"}


def test_select_producers_prefix_treats_wildcards_literally(conn):
    """A "%" in the prefix must match a literal "%", not act as a wildcard."""
    insert_producer(conn, to_slug("50%-off"), "Half off")
    insert_producer(conn, to_slug("acme"), "Acme")

    rows = select_producers(conn, "50%")

    assert {r["slug"] for r in rows} == {"50%-off"}


def test_select_producers_empty_prefix_lists_all(conn):
    """A falsy prefix behaves like no prefix (lists everything)."""
    insert_producer(conn, to_slug("acme"), "Acme")
    insert_producer(conn, to_slug("valio"), "Valio")

    assert len(select_producers(conn, "")) == 2


def test_insert_normalizes_slug(conn):
    insert_producer(conn, to_slug("ACME"), "Acme Corp")
    row = select_producer(conn, to_slug("acme"))
    assert row is not None
    assert row["slug"] == "acme"


def test_select_producer_by_slug(conn):
    insert_producer(conn, to_slug("acme"), "Acme Corp")
    row = select_producer(conn, to_slug("acme"))
    assert row is not None
    assert row["name"] == "Acme Corp"
    assert row["producer_id"] is not None


def test_select_producer_case_insensitive_lookup(conn):
    insert_producer(conn, to_slug("acme"), "Acme Corp")
    row = select_producer(conn, to_slug("ACME"))
    assert row is not None
    assert row["slug"] == "acme"


def test_select_producer_not_found(conn):
    row = select_producer(conn, to_slug("nope"))
    assert row is None


def test_update_producer(conn):
    insert_producer(conn, to_slug("acme"), "Acme Corp")
    update_producer(conn, to_slug("acme"), "Acme Inc")
    row = select_producer(conn, to_slug("acme"))
    assert row is not None
    assert row["name"] == "Acme Inc"


def test_delete_producer(conn):
    insert_producer(conn, to_slug("acme"), "Acme Corp")
    delete_producer(conn, to_slug("acme"))
    assert select_producer(conn, to_slug("acme")) is None


def test_multiple_producers(conn):
    insert_producer(conn, to_slug("acme"), "Acme Corp")
    insert_producer(conn, to_slug("globex"), "Globex Inc")
    rows = select_producers(conn)
    assert len(rows) == 2
