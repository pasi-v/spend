from spend.db import get_connection, init_db


def test_get_connection_returns_working_connection():
    conn = get_connection(":memory:")
    cur = conn.execute("SELECT 1")
    assert cur.fetchone()[0] == 1
    conn.close()


def test_get_connection_enables_foreign_keys():
    conn = get_connection(":memory:")
    result = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert result == 1
    conn.close()


def test_init_db_creates_tables():
    conn = get_connection(":memory:")
    init_db(conn)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "producers" in tables
    assert "products" in tables
    assert "stores" in tables
    assert "vouchers" in tables
    conn.close()
