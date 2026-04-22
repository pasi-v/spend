import pytest
from spend.producers import insert_producer, select_producer
from spend.products import (
    insert_product,
    select_products,
    select_product,
    update_product,
    delete_product,
    require_product,
)


def test_insert_and_select_all(conn):
    insert_product(conn, "milk", "Whole Milk")
    rows = select_products(conn)
    assert len(rows) == 1
    assert rows[0]["slug"] == "milk"
    assert rows[0]["name"] == "Whole Milk"


def test_insert_normalizes_slug(conn):
    insert_product(conn, "MILK", "Whole Milk")
    row = select_product(conn, "milk")
    assert row is not None
    assert row["product_slug"] == "milk"


def test_insert_with_producer(conn):
    insert_producer(conn, "farm", "The Farm")
    producer = select_producer(conn, "farm")
    insert_product(conn, "milk", "Whole Milk", producer["producer_id"])
    row = select_product(conn, "milk")
    assert row["producer_slug"] == "farm"
    assert row["producer_name"] == "The Farm"


def test_insert_without_producer(conn):
    insert_product(conn, "milk", "Whole Milk")
    row = select_product(conn, "milk")
    assert row["producer_slug"] is None


def test_select_product_not_found(conn):
    assert select_product(conn, "nope") is None


def test_update_product(conn):
    insert_producer(conn, "farm", "The Farm")
    producer = select_producer(conn, "farm")
    insert_product(conn, "milk", "Whole Milk")
    update_product(conn, "milk", "Skim Milk", producer["producer_id"])
    row = select_product(conn, "milk")
    assert row["product_name"] == "Skim Milk"
    assert row["producer_slug"] == "farm"


def test_delete_product(conn):
    insert_product(conn, "milk", "Whole Milk")
    delete_product(conn, "milk")
    assert select_product(conn, "milk") is None


def test_require_product_found(conn):
    insert_product(conn, "milk", "Whole Milk")
    row = require_product(conn, "milk")
    assert row["product_slug"] == "milk"


def test_require_product_raises(conn):
    with pytest.raises(ValueError, match="Unknown product: nope"):
        require_product(conn, "nope")
