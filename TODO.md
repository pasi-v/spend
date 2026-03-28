# TODO

## Essential functionality

Add CRUD for voucher headers and voucher lines:
    1. Design table structure.
    2. Create table, and index.
    3. `add` command (voucher header with store and date).
        * UI to add line items => write each to fact table with denormalised header information (store and date)
    4. `list` command (shows line items).
        * Need some kind of filtering functionality
    5. Design and implement `delete` command for line item based on db id.
    6. Design and implement `update` command for line item based on db id.


## Important improvements

Add schema versioning before next schema change.

Figure out a good way to add sub-commands for commands (see also readline auto-complete below).  Maybe some kind of dispatcher.

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
