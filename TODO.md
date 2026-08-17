# TODO

## Important improvements

Add schema versioning before next schema change.

Tests.

Move all I/O from domain functions to shell.py.  They only validate data and call db functions.  Or maybe not, maybe the "domain functions" should not be domain functions at all, and instead just shell dispatches main commands to them, and then they handle I/O.


## Nice to have

_(nothing queued)_


## Experiments

Readline auto-completion is now implemented (sub-commands and slugs, plus the
interactive voucher-line and producer prompts). It re-reads the database on
each completion request — the "every time a completion is requested" option
below — which is simplest and always correct. Revisit only if it becomes slow:

* ~~at the beginning with some in-memory data structure book keeping during running~~
* **every time a completion is requested** ← current approach
* ~~re-read after each slug modification (add, delete, update)~~
