# TODO

Add CRUD for stores:
    1. Design table structure.
    2. Create table, and index for store slug.
    3. `add` command.
    4. `list` command.
    5. `show` command.
    6. `delete` command.
    7. `update` command.

Add schema versioning before next schema change.

Figure out a good way to add sub-commands for commands (see also readline auto-complete below).

Tests.


## Nice to have

Add readline auto-complete for sub-commands, like `producer <TAB>` would offer `add`, `list` etc.

Add readline auto-complete for slugs, like `producer show va<TAB>` would offer every producer starting with `va` as completion.


Test when to read database when auto-completing:

* at the beginning with some in-memory data structure book keeping during running
* every time a completion is requested
* re-read after each slug modification (add, delete, update)
