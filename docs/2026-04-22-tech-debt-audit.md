---
title: "Tech Debt Audit — spend"
date: 2026-04-22
scope: /Users/pv/dev/repos/spend
codebase_size: "~680 LOC, 6 modules"
---

## Overview

The `spend` codebase is a small personal CLI app (~680 lines across 6 Python modules) for tracking spending via an interactive SQLite-backed shell. The foundation is solid — parameterized queries, sensible module boundaries, stdlib-only — but there is zero test infrastructure, significant code duplication, and mixed concerns between I/O and domain logic. The overall picture is a project where refactoring is possible but currently risky because nothing is verified by tests.

Prioritization uses: **Priority = (Impact + Risk) × (6 − Effort)**, scores 1–5 each.

---

## Prioritized Debt Items

### ~~P1 — Zero Test Coverage~~ ✅ Done
**Category**: Test debt  
**Score**: (5 + 5) × (6 − 2) = **40**

There are no test files, no test framework, and no coverage reporting anywhere in the repo. All six modules (`db.py`, `shell.py`, `producers.py`, `products.py`, `stores.py`, `vouchers.py`) are completely untested. This makes any refactoring dangerous — there is no safety net to catch regressions.

*Fix*: Add `pytest` with a `pyproject.toml`, write unit tests for each domain module using an in-memory SQLite database (`":memory:"`). Target 60% coverage before touching anything else.

---

### P2 — Code Duplication Across CRUD Modules
**Category**: Code debt  
**Score**: (4 + 3) × (6 − 3) = **21**

The same structural patterns appear four times — once per entity (producer, product, store, voucher):

- `schema()` — table DDL template
- `select_*()` — query boilerplate
- `do_list_*()` — fetch + print loop
- `do_show_*()` — fetch-by-slug + print
- `do_delete_*()` — confirm + delete
- Slug normalization: `.lower()` called explicitly at every query site (16+ times across the four modules)

*Fix*: Extract a generic `BaseRepository` class or a set of helper functions (`list_entities`, `show_entity`, etc.). Normalize slugs in a single place (a `Slug` type or property). This is a medium-effort refactor but has a high payoff for maintainability.

---

### P3 — Mixed I/O and Domain Logic
**Category**: Architecture debt  
**Score**: (4 + 3) × (6 − 3) = **21**

`input()` calls are scattered throughout domain modules (`products.py:106`, `stores.py:67`, `producers.py:69`). The function `collect_voucher_lines()` in `shell.py` mixes stdin reading, string parsing, and a live database query (`require_product`) in one block. This is explicitly acknowledged in `TODO.md` line 9: *"Move all I/O from domain functions to shell.py"*.

*Fix*: Domain functions should accept plain values and return results. All `input()` calls belong in `shell.py`. This is the most architecturally meaningful refactor — it decouples the domain from the UI and enables testing.

---

### ~~P4 — Wildcard Import~~ ✅ Done
**Category**: Code debt  
**Score**: (3 + 3) × (6 − 1) = **30** (low effort, quick win)

`products.py:1` has `from producers import *`, which pulls in the entire `producers` namespace. This creates hidden dependencies, pollutes the module namespace, and will silently break if `producers` is ever renamed or restructured.

*Fix*: One line — replace with `from producers import require_producer` (or whichever symbol is actually used). Quick win.

---

### ~~P5 — Inadequate Error Handling~~ ✅ Done
**Category**: Code debt  
**Score**: (3 + 3) × (6 − 2) = **24**

`shell.py:237–248` catches only `sqlite3.IntegrityError` and re-raises everything else with a bare `raise`, losing context. Other DB errors (`OperationalError`, `ProgrammingError`) crash with an unformatted traceback. User-facing errors are plain `print()` statements with no log level, no timestamp, and no stack trace preservation. The debug prints flagged in `shell.py:31` (`# TODO: Remove these debug prints`) are still present.

*Fix*: Introduce `logging` in place of `print()` for errors. Expand exception handling to cover `sqlite3.OperationalError`. Remove or gate the debug prints behind a `--verbose` flag.

---

### ~~P6 — No Type Hints~~ ✅ Done
**Category**: Code debt  
**Score**: (3 + 2) × (6 − 2) = **20**

Type hints exist on roughly 2–3% of function signatures (18 instances across 6 files). The majority of functions — especially in `shell.py` and the CRUD modules — have no parameter or return type annotations. This limits IDE support and makes refactoring harder to validate.

*Fix*: Add type hints incrementally, starting with the domain modules (`producers.py`, `products.py`, etc.), then `shell.py`. Run `mypy` in strict mode once coverage is added. Low per-function effort, medium total effort.

---

### P7 — Hardcoded Values
**Category**: Code debt  
**Score**: (2 + 2) × (6 − 1) = **20**

The database filename `"spend.db"` is hardcoded in `main.py:6` and as a default parameter in `db.py:7`. The date format `"%Y-%m-%d"` is a string literal used in multiple places. Currency conversion (`* 100`, `/ 100`) is scattered across `vouchers.py` with no named constant or abstraction.

*Fix*: Define a `DATE_FORMAT` constant. Add a `Decimal`-to-cents helper. Accept the database path via a CLI argument or environment variable.

---

### P8 — No Schema Versioning / Migration Framework
**Category**: Architecture debt  
**Score**: (3 + 4) × (6 − 3) = **21**

There is no migration mechanism. Schema changes require manual SQL edits and will silently fail or corrupt existing databases. `TODO.md:5` flags this explicitly: *"Add schema versioning before next schema change"*. The presence of `spend.bak.db` suggests manual backup was used at some point before a schema change.

*Fix*: Add Alembic (or even a simple hand-rolled migration runner) before the next schema change. Alembic is a small addition for a stdlib-only project but a significant safety improvement.

---

### ~~P9 — Missing Project Metadata & Tooling~~ ✅ Done
**Category**: Infrastructure / Documentation debt  
**Score**: (2 + 2) × (6 − 1) = **20**

There is no `pyproject.toml`, `setup.py`, or `requirements.txt`. The Python version requirement is implicit (3.10+ due to match/case syntax). There is no pre-commit configuration, no linter setup (ruff, flake8), and no formatter config (black, ruff format).

*Fix*: Add a minimal `pyproject.toml` specifying `python = ">=3.10"`, dev dependencies (`pytest`, `mypy`, `ruff`), and a `[tool.ruff]` section. This is a single small file that unlocks the rest of the toolchain.

---

### ~~P10 — README and Documentation~~ ✅ Done
**Category**: Documentation debt  
**Score**: (2 + 1) × (6 − 1) = **15**

The README is two lines. There is no usage guide, no command reference, no schema documentation, and no ER diagram. The SQL examples in `queries/` are good but are not mentioned anywhere.

*Fix*: Expand README with: installation steps, available commands with examples, schema overview, and a pointer to the `queries/` folder. Low priority for a personal tool, but useful for future self.

---

## Phased Remediation Plan

This plan is designed to be done **alongside feature work** — no phase requires a freeze.

### ~~Phase 1 — Unblock Refactoring (1–2 sessions)~~ ✅ Done
Items: ~~P1~~, ~~P4~~, ~~P9~~

Add `pyproject.toml`, fix the wildcard import, write tests for the four domain modules using in-memory SQLite. This is the prerequisite for everything else — nothing else is safe to change until there is a test harness.

### Phase 2 — Clean Up Code Structure (2–3 sessions)
Items: ~~P5~~, ~~P6~~, P7

Fix error handling and remove debug prints. Add type hints to domain modules. Extract date format and currency constants. These are surgical changes, each independently safe once Phase 1 is done.

### Phase 3 — Architectural Improvements (3–4 sessions)
Items: P2, P3, P8

Extract CRUD patterns into shared helpers. Move `input()` calls out of domain modules. Add a migration runner before the next schema change. These are the most impactful changes for long-term maintainability.

### Phase 4 — Polish (ongoing)
Items: ~~P10~~

Improve README, add readline auto-completion (from `TODO.md`), document schema with an ER diagram.

---

## Summary Scorecard

| # | Item | Category | Priority Score | Phase |
|---|------|----------|---------------|-------|
| P1 | Zero test coverage | Test | 40 | 1 |
| P4 | Wildcard import | Code | 30 | 1 |
| P5 | Inadequate error handling | Code | 24 | 2 |
| P2 | CRUD code duplication | Code | 21 | 3 |
| P3 | Mixed I/O and domain logic | Architecture | 21 | 3 |
| P8 | No schema versioning | Architecture | 21 | 3 |
| P6 | No type hints | Code | 20 | 2 |
| P7 | Hardcoded values | Code | 20 | 2 |
| P9 | Missing project metadata | Infrastructure | 20 | 1 |
| P10 | Minimal README | Documentation | 15 | 4 |
