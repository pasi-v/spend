#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
.venv/bin/ruff check .
.venv/bin/mypy spend tests
./run_tests.sh
