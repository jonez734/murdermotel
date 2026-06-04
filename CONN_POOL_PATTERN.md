# Database Connection Pool Pattern

This documents the proper pattern for database connections in Murder Motel.

## Required Pattern for `.save()` Methods

All save methods in classes (Player, Room, Item, Thief, etc.) must follow this pattern:

```python
def save(self, mogrify=False, **kwargs):
    def _work(conn):
        # Database operations here
        # Use conn=conn for all database.* calls
        # Use commit=False on upsert/insert/update calls
        return True

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool") or self.pool
        if pool is None:
            io.echo(f"{self.classname}.save.100: pool is None", level="error")
            return False
        with database.connect(self.args, pool=pool) as conn:
            return _work(conn)
    else:
        return _work(conn)
```

## Required Pattern for Standalone Functions

Standalone functions (not methods) must follow this pattern:

```python
def some_function(args, some_id, **kwargs):
    def _work(conn):
        # Database operations here
        # Use commit=False on database.* calls
        return result

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"module.function.100: {pool=}", level="error")
            return default_value  # False, [], None, etc.
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)
```

## Key Points

1. **Accept `**kwargs`** - allows caller to pass existing conn or pool
2. **Check conn first**: `conn = kwargs.get("conn", None)` - existing connection takes priority
3. **Check pool second**: for .save() use `kwargs.get("pool") or self.pool`, for standalone use `kwargs.get("pool", None)`
4. **pool is None is fatal**: never call `database.getpool(args)` as fallback - callers must pass pool
5. **Use nested `_work(conn)`**: keeps connection handling clean
6. **Pass `conn=conn`**: to all database.* function calls
7. **Use commit=False**: on database.upsert/insert/update calls to defer commit
8. **No explicit conn.commit()**: context manager handles commit automatically

## Context Manager Handles Commit

The `database.connect()` context manager automatically:
- Sets `conn.autocommit = False` on connection acquisition
- Commits on successful exit (when auto_commit=True, the default)
- Returns connection to pool
- Rolls back on exception

## Why No Explicit conn.commit()?

Explicit `conn.commit()` after using the context manager causes problems:

1. Context manager already committed via `conn.commit()` in its finally block
2. Calling `conn.commit()` again means commit happens AFTER context manager already returned the connection to pool
3. Pool sees INTRANS state (transaction still active) and logs "rolling back returned connection"

The fix: remove all explicit `conn.commit()` calls. Let the context manager handle it.

## Refinements (2026-06-03)

### Explicit conn.commit() Causes INTRANS Rollback

After the context manager yields and the `finally` block runs:
1. `if auto_commit: conn.commit()` executes
2. `pool.putconn(conn)` returns connection to pool
3. Any subsequent `conn.commit()` happens AFTER connection is back in pool
4. Pool sees INTRANS status and rolls back, logging warning

**Fix**: Never call `conn.commit()` after using `with database.connect(...)`.

### For .save() Methods - Prefer kwargs.pool over self.pool

```python
pool = kwargs.get("pool") or self.pool
```

This allows:
- Callers to pass pool via kwargs (preferred - avoids new connection)
- Falls back to self.pool if not provided

### For Standalone Functions - pool=None is Fatal

If pool is None, the caller is misbehaving - don't silently fix with getpool():
- Log error with pool value shown: `io.echo(f"module.function.100: {pool=}", level="error")`
- Return default/failure value
- Let the error bubble up so the caller can fix their code

## Use upsert Instead of Update+Insert

Prefer `database.upsert()` over separate update/insert for atomic saves:

```python
database.upsert(
    args,
    "schema.table",
    {"id": self.id, "name": self.name},
    conflict_columns=["id"],  # unique constraint columns
    conn=conn,
    commit=False,
)
```

## Files Following This Pattern

- `player.py` - Player.save()
- `obj.py` - Obj.save()
- `thief.py` - Thief.save()
- `rabidwolf.py` - RabidWolf.save()
- `bot.py` - Bot.save()
- `room.py` - Room.save()
- `item.py` - Item.save()
- `startup.py` - main(), _populate_rooms(), _check_orphan_items()