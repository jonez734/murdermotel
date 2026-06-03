# Writing Integration Tests for Murdermotel's Take/Leave (T/L) System

## Context

This document describes the process of writing end-to-end integration tests for
the `[T]`ake and `[L]`eave item flow in murdermotel's play loop
(`play.py:519-575`).

## The T/L Flow

In the play loop, the player selects `T` to take an item from the room or `L`
to leave an item:

```python
# play.py:519-547  (take)
itemindex = room.finditem(itemname)
item = room.items[itemindex]
del room.items[itemindex]
player.items.append(item)
player.save(pool=pool)
room.save(pool=pool)

# play.py:548-575  (leave)
itemindex = player.finditem(itemname)
item = player.items[itemindex]
del player.items[itemindex]
room.items.append(item)
player.save(pool=pool)
room.save(pool=pool)
```

The persistence layer is two join tables:

- `murdermotel.map_item_room` — items currently in a room
- `murdermotel.map_item_player` — items currently held by a player

Taking an item moves a row from the former to the latter. Leaving reverses the
direction.

## The Circular Import Problem (Fixed)

murdermotel had a circular import chain:

```
lib.py:20  Item = libitem.Item    ← runs at import time
item.py:3  from . import lib as libmm
lib.py:1-20                      ← libitem.Item not yet defined
```

The fix was simple: remove `Item = libitem.Item` from `lib.py:20`. All call
sites were updated to use `libitem.Item(args, ...)` directly. After the fix,
`from murdermotel import room, player` works cleanly.

## Testing Strategy: CONN_POOL_PATTERN

All murdermotel database functions follow the **CONN_POOL_PATTERN**: they
accept `**kwargs` to receive either an existing `conn` (connection) or a `pool`
(connection pool). The pattern is:

```python
def some_function(args, some_id, **kwargs):
    def _work(conn):
        # Database operations here
        return result

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            return default_value
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)
```

**Key rule for testing**: `conn` is passed via kwargs. Tests must do the same.
When a test opens a connection with `pool.getconn()` and passes it as
`conn=conn` through multiple function calls, all operations share the same
transaction — commits from `_place_item_*` helpers are visible to subsequent
`libplayer.load()` calls within the same connection.

This means: wrap each logical test block in `with test_pool.getconn() as conn:`
and pass `conn` through all function calls. Never call `.save()` without
passing the connection, because `.save()` opens its own connection if `conn`
is not provided.

## Bugs Found While Writing Tests

### Bug 1: `libitem.load` fails when called without `pool` in kwargs

`player.getitems()` called `libitem.load(args, name, serial=serial)` without
passing pool or conn. Since the function's own kwargs had no pool (it received
only args and serial), `item.load()` logged `pool=None` and returned `None`.
This silently broke all L-path tests.

Fix: pass `conn` to `libitem.load` from within `getitems`:

```python
item = libitem.load(args, rec["itemname"], serial=serial, conn=conn)
```

### Bug 2: `player.load()` not forwarding conn to `getitems()`

`player.load()` called `getitems(args, moniker, **kwargs)` which passed
`pool=pool, conn=None` (conn got lost in the **kwargs shuffle). `getitems()`
then opened its own connection, which couldn't see items placed in the test's
connection.

Fix: `player.load()` now calls `getitems(args, moniker, conn=conn)` explicitly,
extracting conn before calling `getitems`.

### Bug 3: `item.load()` / `room.load()` — return None/False inside debug-only block

In `item.py:load()` and `room.py:load()`, the `return None` / `return False`
for "not found" was inside `if args.debug is True:`, so in non-debug mode
execution continued with `rec = None` (fetchone returned None or rowcount was 0
but no early return), causing cascading downstream failures.

Fix: move `return None` outside the debug conditional.

### Bug 4: `psycopg` `fetchmany()` defaulting to arraysize=1

In `player.getitems()`, `cur.fetchmany()` without a size returns only 1 row at
a time. Changed to `cur.fetchall()`.

## Test Coverage

| Test | Verifies |
|------|----------|
| `test_take_item_from_room` | Room→Player transfer via Room/Player API |
| `test_leave_item_from_player` | Player→Room transfer via Room/Player API |
| `test_round_trip_take_then_leave` | Item returns to same room |
| `test_round_trip_leave_then_take` | Item returns to player |
| `test_take_nonexistent_item` | finditem returns None for missing item |
| `test_leave_nonexistent_item` | finditem returns None for missing item |
| `test_take_from_empty_room` | Zero-count assertion on empty room |
| `test_leave_with_empty_inventory` | Zero-count assertion on empty inventory |
| `test_multiple_rooms_take_leave` | Three rooms; take from middle, leave in north |
| `test_max_items_constant` | MAXITEMSPERPLAYER == 5 |
| `test_take_item_by_title` | finditem matches item.title |
| `test_take_via_mocked_io` | Full T prompt flow with mocked io.inputstring |
| `test_leave_via_mocked_io` | Full L prompt flow with mocked io.inputstring |
| `test_take_aborted_via_mocked_io` | Empty input aborts, no state change |

## Files Modified

```
src/murdermotel/
  lib.py           — Removed Item alias (line 20), use libitem.Item
  player.py        — getitems passes conn to libitem.load; load passes conn explicitly
  item.py          — return None unconditional (not debug-only)
  room.py          — return False unconditional (not debug-only)

src/murdermotel/tests/
  conftest.py              — DB-backed fixtures with deferred imports
  test_take_leave_integration.py  — 14 tests, all passing
  TEST_TAKE_LEAVE.md       — this document
```

## Running the Tests

```bash
cd /home/opencode/data/work/murdermotel
python -m pytest src/murdermotel/tests/test_take_leave_integration.py -v
```

Environment variables (all optional):

| Variable | Default | Purpose |
|----------|---------|---------|
| `MM_TEST_DBNAME` | `zoid6test` | Database name |
| `MM_TEST_DBHOST` | `/var/run/postgresql` | PostgreSQL socket path |
| `MM_TEST_DBPORT` | `5432` | Port |
| `MM_TEST_DBUSER` | `opencode` | Username |