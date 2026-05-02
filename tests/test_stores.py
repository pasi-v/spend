import pytest

from spend.slug import to_slug
from spend.stores import (
    delete_store,
    insert_store,
    require_store,
    select_store,
    select_stores,
    update_store,
)


def test_insert_and_select_all(conn):
    insert_store(conn, to_slug("lidl"), "Lidl")
    rows = select_stores(conn)
    assert len(rows) == 1
    assert rows[0]["slug"] == "lidl"
    assert rows[0]["name"] == "Lidl"


def test_insert_normalizes_slug(conn):
    insert_store(conn, to_slug("LIDL"), "Lidl")
    row = select_store(conn, to_slug("lidl"))
    assert row is not None
    assert row["slug"] == "lidl"


def test_select_store_by_slug(conn):
    insert_store(conn, to_slug("lidl"), "Lidl")
    row = select_store(conn, to_slug("lidl"))
    assert row is not None
    assert row["name"] == "Lidl"
    assert row["store_id"] is not None


def test_select_store_case_insensitive_lookup(conn):
    insert_store(conn, to_slug("lidl"), "Lidl")
    row = select_store(conn, to_slug("LIDL"))
    assert row is not None
    assert row["slug"] == "lidl"


def test_select_store_not_found(conn):
    assert select_store(conn, to_slug("nope")) is None


def test_update_store(conn):
    insert_store(conn, to_slug("lidl"), "Lidl")
    update_store(conn, to_slug("lidl"), "Lidl Finland")
    row = select_store(conn, to_slug("lidl"))
    assert row is not None
    assert row["name"] == "Lidl Finland"


def test_delete_store(conn):
    insert_store(conn, to_slug("lidl"), "Lidl")
    delete_store(conn, to_slug("lidl"))
    assert select_store(conn, to_slug("lidl")) is None


def test_multiple_stores(conn):
    insert_store(conn, to_slug("lidl"), "Lidl")
    insert_store(conn, to_slug("prisma"), "Prisma")
    rows = select_stores(conn)
    assert len(rows) == 2


def test_require_store_found(conn):
    insert_store(conn, to_slug("lidl"), "Lidl")
    row = require_store(conn, to_slug("lidl"))
    assert row["slug"] == "lidl"


def test_require_store_raises(conn):
    with pytest.raises(ValueError, match="Unknown store: nope"):
        require_store(conn, to_slug("nope"))
