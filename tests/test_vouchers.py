from datetime import date
from decimal import Decimal

from spend.producers import insert_producer, select_producer
from spend.products import insert_product, select_product
from spend.stores import insert_store, select_store
from spend.vouchers import (
    insert_voucher_line,
    select_vouchers,
    select_voucher,
    delete_voucher,
    do_add_voucher,
)


def _seed(conn):
    """Insert a producer, product, and store for voucher tests."""
    insert_producer(conn, "farm", "The Farm")
    producer = select_producer(conn, "farm")
    insert_product(conn, "milk", "Whole Milk", producer["producer_id"])
    insert_store(conn, "lidl", "Lidl")


def test_insert_and_select_all(conn):
    _seed(conn)
    product = select_product(conn, "milk")
    store = select_store(conn, "lidl")
    insert_voucher_line(conn, product["product_id"], 299, date(2026, 1, 15), store["store_id"])
    rows = select_vouchers(conn)
    assert len(rows) == 1
    assert rows[0]["amount_cents"] == 299
    assert rows[0]["product_slug"] == "milk"
    assert rows[0]["store_slug"] == "lidl"
    assert rows[0]["date"] == "2026-01-15"


def test_select_voucher_by_id(conn):
    _seed(conn)
    product = select_product(conn, "milk")
    store = select_store(conn, "lidl")
    insert_voucher_line(conn, product["product_id"], 500, date(2026, 2, 1), store["store_id"])
    rows = select_vouchers(conn)
    vid = rows[0]["voucher_id"]
    row = select_voucher(conn, vid)
    assert row["amount_cents"] == 500
    assert row["product_slug"] == "milk"


def test_select_voucher_not_found(conn):
    assert select_voucher(conn, 999) is None


def test_delete_voucher(conn):
    _seed(conn)
    product = select_product(conn, "milk")
    store = select_store(conn, "lidl")
    insert_voucher_line(conn, product["product_id"], 100, date(2026, 3, 1), store["store_id"])
    rows = select_vouchers(conn)
    vid = rows[0]["voucher_id"]
    delete_voucher(conn, vid)
    assert select_voucher(conn, vid) is None


def test_do_add_voucher(conn):
    _seed(conn)
    lines = [("milk", Decimal("2.99"))]
    do_add_voucher(conn, date(2026, 4, 1), "lidl", lines)
    rows = select_vouchers(conn)
    assert len(rows) == 1
    assert rows[0]["amount_cents"] == 299
    assert rows[0]["store_slug"] == "lidl"


def test_do_add_voucher_multiple_lines(conn):
    _seed(conn)
    insert_product(conn, "bread", "Rye Bread")
    lines = [("milk", Decimal("2.99")), ("bread", Decimal("1.50"))]
    do_add_voucher(conn, date(2026, 4, 1), "lidl", lines)
    rows = select_vouchers(conn)
    assert len(rows) == 2
