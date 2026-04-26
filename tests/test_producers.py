from spend.producers import (
    delete_producer,
    insert_producer,
    select_producer,
    select_producers,
    update_producer,
)


def test_insert_and_select_all(conn):
    insert_producer(conn, "acme", "Acme Corp")
    rows = select_producers(conn)
    assert len(rows) == 1
    assert rows[0]["slug"] == "acme"
    assert rows[0]["name"] == "Acme Corp"


def test_insert_normalizes_slug(conn):
    insert_producer(conn, "ACME", "Acme Corp")
    row = select_producer(conn, "acme")
    assert row is not None
    assert row["slug"] == "acme"


def test_select_producer_by_slug(conn):
    insert_producer(conn, "acme", "Acme Corp")
    row = select_producer(conn, "acme")
    assert row["name"] == "Acme Corp"
    assert row["producer_id"] is not None


def test_select_producer_case_insensitive_lookup(conn):
    insert_producer(conn, "acme", "Acme Corp")
    row = select_producer(conn, "ACME")
    assert row is not None
    assert row["slug"] == "acme"


def test_select_producer_not_found(conn):
    row = select_producer(conn, "nope")
    assert row is None


def test_update_producer(conn):
    insert_producer(conn, "acme", "Acme Corp")
    update_producer(conn, "acme", "Acme Inc")
    row = select_producer(conn, "acme")
    assert row["name"] == "Acme Inc"


def test_delete_producer(conn):
    insert_producer(conn, "acme", "Acme Corp")
    delete_producer(conn, "acme")
    assert select_producer(conn, "acme") is None


def test_multiple_producers(conn):
    insert_producer(conn, "acme", "Acme Corp")
    insert_producer(conn, "globex", "Globex Inc")
    rows = select_producers(conn)
    assert len(rows) == 2
