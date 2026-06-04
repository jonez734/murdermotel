# Murder Motel Database Schema

## Overview

PostgreSQL schema for the Murder Motel game. Uses explicit joins instead of table inheritance for type modeling.

## Module Specifications

Detailed specifications for each game module:

| File | Description |
|------|-------------|
| [SPEC_room.md](SPEC_room.md) | Room module (locations, exits) |
| [SPEC_player.md](SPEC_player.md) | Player module (characters, inventory) |
| [SPEC_item.md](SPEC_item.md) | Item module (weapons, components, traps) |
| [SPEC_obj.md](SPEC_obj.md) | Base object classes and registry |
| [SPEC_npc.md](SPEC_npc.md) | NPC modules (RabidWolf, Thief) |

### Maintenance Modules (sysop-only)

| Module | Description |
|--------|-------------|
| `housekeeping` | Maintenance menu with Setup, Edit, Weapon List, Quit |
| `weaponlist` | Sysop-only tool showing components and recipe info |

The `weaponlist` module provides two options:
- **C** - Components: Lists all components with their room locations
- **R** - Recipes: Shows each weapon recipe with its two components and room numbers (or "unplaced" if not in any room)

## Tables

### Core Tables

| Table | Description |
|-------|-------------|
| `murdermotel.playground` | Game rooms/locations |
| `murdermotel.player` | Game players |
| `murdermotel.item` | Items (weapons, booby traps) |
| `murdermotel.npc` | NPCs (wolves, thieves) |

### Item Subtypes (via join)

| Table | Parent | Additional Columns |
|-------|--------|-------------------|
| `murdermotel.boobytrap` | `item` | `running`, `timer` |

### NPC Subtypes (via join)

| Table | Parent | Additional Columns |
|-------|--------|-------------------|
| `murdermotel.rabidwolf` | `npc` | `roomid`, `healthpoints` |
| `murdermotel.thief` | `npc` | `bag` (citext[]), `roomid`, `healthpoints` |

### Mapping Tables

| Table | Purpose |
|-------|---------|
| `murdermotel.map_item_player` | Items held by players |
| `murdermotel.map_item_room` | Items placed in rooms |
| `murdermotel.map_item_thief` | Items stolen by the thief |

### Weapon System

| Table | Purpose |
|-------|---------|
| `murdermotel.weapon_recipe` | Weapon definitions: name, components, count, defaults |

## Design Decisions

### Kind Column Pattern

Each parent table uses a `kind` column with CHECK constraint to enforce valid subtypes:

- `item.kind` ∈ {'weapon', 'boobytrap', 'component', 'defense', 'item'}
- `npc.kind` ∈ {'wolf', 'thief'}

### Weapon Mode

The `WEAPON_MODE` config in `lib.py` controls weapon distribution:

| Mode | Behavior |
|------|----------|
| `components` | Distribute components only. Players assemble weapons via `weapon_recipe`. |
| `complete` | Distribute pre-built `kind='weapon'` items directly into rooms. |
| `both` | Both: components + complete weapons placed in rooms. |

### Instance State

Each weapon instance in `murdermotel.item` has a `state` JSONB column that can diverge from the recipe defaults. The `weapon_recipe.state` column provides default values copied into each instance at generation time.

## Save Pattern (CONN_POOL_PATTERN)

All `save()` methods follow a consistent pattern for transaction management:

1. `_work(conn)` nested function performs DB operations
2. All database.* calls use `commit=False` to defer commit
3. Context manager handles commit on successful exit
4. No explicit `conn.commit()` - context manager handles it

```python
def save(self, **kwargs):
    def _work(conn):
        # DB operations with commit=False
        return True

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool") or self.pool
        if pool is None:
            io.echo(f"mm.{self.classname}.save.100: {pool=}", level="error")
            return False
        with database.connect(self.args, pool=pool) as conn:
            return _work(conn)
    else:
        return _work(conn)
```

**Critical**: Explicit `conn.commit()` after context manager causes INTRANS rollback. Never call `conn.commit()` when using `with database.connect()`.

### Read-Only Queries and Autocommit

For read-only queries (SELECT COUNT, SELECT ... LIMIT, etc.), use `autocommit=True` to avoid INTRANS warnings:

```python
def count(moniker, args, **kwargs):
    pool, conn, we_created = _resolve_conn(
        args, kwargs.get("pool"), kwargs.get("conn"), autocommit=True
    )
    if conn is None:
        return None
    try:
        with database.cursor(conn) as cur:
            cur.execute("SELECT COUNT(*) FROM ...")
            return cur.fetchone()
    finally:
        if we_created and pool is not None:
            pool.putconn(conn)
```

**When to use autocommit**:
- `autocommit=True`: Read-only queries (SELECT COUNT, SELECT ... LIMIT)
- `autocommit=False`: Write operations (INSERT, UPDATE, DELETE) needing transaction control

The `bbsengine6.notify.count()` function uses `autocommit=True` to eliminate INTRANS warnings from the notify subsystem.

## Fatal DB Errors in Module main()

All module `main()` functions are decorated with `@fatal_on_db_error` from `bbsengine6.io`.
This makes DB/connection errors fatal (exit 1) rather than silently failing:

```python
from bbsengine6.io import fatal_on_db_error

@fatal_on_db_error
def main(args, **kwargs):
    with database.connect(args, pool=pool) as conn:
        _work(conn)
```

The decorator catches:
- `psycopg.OperationalError` - connection refused, pool exhausted, server down
- `psycopg.InterfaceError` - connection closed unexpectedly

On fatal error: traceback is printed via `echo_traceback()` and `sys.exit(1)` is called.

Other exceptions (ValueError, KeyError, KeyboardInterrupt) propagate normally.

**Applied to**: bot, player, maintenance, thief, rabidwolf, boobytrap, item, room,
weaponlist, housekeeping, traproom, startup, play, lobby.

## Loading Order

```
schema.sql
  → player.sql
  → playground.sql
  → item.sql
    → weapon_recipe.sql (weapon.sql)
    → boobytrap.sql
  → npc.sql
    → wolf.sql
    → thief.sql
```