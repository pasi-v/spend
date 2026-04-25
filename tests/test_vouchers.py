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
    to_cents,
    from_cents,
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


def test_to_cents_preserves_fractional_part():
    # Regression: int(Decimal("2.99")) truncates to 2 before * 100, giving 200.
    assert to_cents(Decimal("2.99")) == 299


def test_to_cents_whole_euros():
    assert to_cents(Decimal("5")) == 500
    assert to_cents(Decimal("5.00")) == 500


def test_to_cents_zero():
    assert to_cents(Decimal("0")) == 0


def test_to_cents_single_decimal():
    assert to_cents(Decimal("1.5")) == 150


def test_to_cents_rounds_half_up():
    # Sub-cent input should round half-up, not truncate or banker's-round.
    assert to_cents(Decimal("12.345")) == 1235
    assert to_cents(Decimal("12.344")) == 1234
    assert to_cents(Decimal("0.005")) == 1
    # Banker's rounding would give 12 here; ROUND_HALF_UP gives 13.
    assert to_cents(Decimal("0.125")) == 13


def test_from_cents_basic():
    assert from_cents(299) == Decimal("2.99")
    assert from_cents(0) == Decimal("0")
    assert from_cents(100) == Decimal("1")


def test_from_cents_round_trip():
    for amount in ["0", "0.01", "1.50", "2.99", "12345.67"]:
        d = Decimal(amount)
        assert from_cents(to_cents(d)) == d
