# TODO

## Important improvements

Add schema versioning before next schema change.

Tests.

Move all I/O from domain functions to shell.py.  They only validate data and call db functions.  Or maybe not, maybe the "domain functions" should not be domain functions at all, and instead just shell dispatches main commands to them, and then they handle I/O.


## Nice to have

Add readline auto-complete for sub-commands, like `producer <TAB>` would offer `add`, `list` etc.

Add readline auto-complete for slugs, like `producer show va<TAB>` would offer every producer starting with `va` as completion.


## Experiments

Test when to read database when auto-completing:

* at the beginning with some in-memory data structure book keeping during running
* every time a completion is requested
* re-read after each slug modification (add, delete, update)
