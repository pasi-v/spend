# spend

Personal spending data input program. A small interactive shell that stores
producers, products, stores, and vouchers in a local SQLite database
(`spend.db`).

## Installation

Requires Python 3.10+ (uses `match`/`case`). Stdlib only at runtime — the
development dependencies are only needed for tests and linting.

```sh
git clone <this repo>
cd spend
pip install -r dev-requirements.txt   # optional, for tests
```

The database file `spend.db` is created in the current working directory the
first time the program starts.

## Running

```sh
./run.sh
```

Use `--verbose` to enable debug output:

```sh
./run.sh --verbose
```

Inside the shell, type `help` or `?` to list commands, or `help <command>`
for details. Exit with `quit` or `exit`.

## Commands

All entity commands follow the same shape: `<entity> <action> [args...]`.
Slugs are case-insensitive (they are lowercased before being stored).

### Producers

```
producer add    <slug> <name>      Add a producer
producer list                      List all producers
producer show   <slug>             Show one producer
producer update <slug>             Prompt for new name and update
producer delete <slug>             Delete a producer
```

Example:

```
(spend) producer add valio "Valio Oy"
(spend) producer list
```

### Products

Products may optionally be linked to a producer.

```
product add    <slug> <name> [<producer_slug>]
product list
product show   <slug>
product update <slug>              Prompt for new name and producer
product delete <slug>
```

Example:

```
(spend) product add maito "Maito 1 l" valio
(spend) product show maito
```

### Stores

```
store add    <slug> <name>
store list
store show   <slug>
store update <slug>                Prompt for new name
store delete <slug>
```

Example:

```
(spend) store add prisma "Prisma Kaleva"
```

### Vouchers

A voucher is one receipt — a date and a store, with one or more product
lines. Amounts are entered in euros (e.g. `3.49`) and stored internally as
integer cents.

```
voucher add    <YYYY-MM-DD> <store_slug>   Then enter lines interactively
voucher list
voucher show   <voucher_id>
voucher delete <voucher_id>
```

Example:

```
(spend) voucher add 2026-04-22 prisma
Adding voucher lines: <product_slug> <amount in €.cc> (empty line to end)
maito 1.29
leipa 3.49

(spend) voucher list
```

Vouchers have no slug — use the integer `voucher_id` (shown by `voucher
list`) to `show` or `delete` them.

## Schema

Four tables: `producers`, `products`, `stores`, `vouchers`. Foreign keys are
enforced (`PRAGMA foreign_keys = 1`) with `ON DELETE RESTRICT` everywhere,
so you cannot delete a producer that still has products or a product/store
that still appears on a voucher.

See [`docs/spend_er_diagram.mermaid`](docs/spend_er_diagram.mermaid) for the
full ER diagram. Summary:

- `producers (producer_id, slug UNIQUE, name)`
- `products (product_id, slug UNIQUE, name, producer_id → producers)`
- `stores (store_id, slug UNIQUE, name)`
- `vouchers (voucher_id, date, amount_cents, product_id → products, store_id → stores)`

The schema is defined inline in the domain modules (`spend/producers.py`,
`spend/products.py`, `spend/stores.py`, `spend/vouchers.py`) via a
`schema()` function each, and applied by `spend/db.py:init_db()` on
startup.

## Reporting queries

Ready-made analytical SQL lives in [`queries/`](queries/):

- [`top-producers.sql`](queries/top-producers.sql) — total spend per producer
- [`top-products.sql`](queries/top-products.sql)  — total spend per product
- [`top-stores.sql`](queries/top-stores.sql)    — total spend per store

Run them with the `sqlite3` CLI:

```sh
sqlite3 spend.db < queries/top-products.sql
```

## Development

```sh
pip install -r dev-requirements.txt
./run_tests.sh
```

Tests use in-memory SQLite (`":memory:"`) and live under `tests/`. Coverage
is enforced at 60% via `pyproject.toml`. Type checking (`mypy`) and linting
(`ruff`) are also configured in `pyproject.toml`.

## License

GPL-3.0-only. See [`LICENSE`](LICENSE).
