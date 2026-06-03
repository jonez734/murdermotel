# SPEC_item.md - Murder Motel Item Module

## Overview

Item module for the Murder Motel game. Manages items (weapons, components, booby traps).

## Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `init` | `(args, obj=None, room=None, **kwargs) -> bool` | Module initialization |
| `access` | `(args, op, **kwargs) -> bool` | Check if operation is permitted |
| `buildargs` | `(args, obj=None, room=None, **kwargs)` | Build command-line arguments |
| `main` | `(args, **kwargs) -> bool` | Main entry point |
| `load` | `(args, name, **kwargs)` | Load item by name |
| `exists` | `(args, name, **kwargs) -> bool` | Check if item exists |
| `count` | `(args, **kwargs) -> int` | Get total item count |
| `getcount` | `(args, kind, **kwargs) -> int` | Get count by kind |
| `build` | `(args, rec: dict, **kwargs) -> Item` | Build Item from record |

## Item Class

```python
class Item:
    args: object
    kind: str
    modulepath: str
    name: str
    serial: int
    title: str | None
    type: str
    usemessages: list
    table: str
    pool: object
    state: dict | str | None
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `short` | `() -> str` | Get short item description |
| `buildrec` | `()` | Build database record |
| `save` | `(mogrify=False, **kwargs)` | Save item to database (uses CONN_POOL_PATTERN: context manager handles commit) |

## CONN_POOL_PATTERN

All database save/load methods use the standard bbsengine6 CONN_POOL_PATTERN:

```python
def save(self, mogrify=False, **kwargs):
    def _work(conn):
        # Database operations with conn, commit=False
    
    conn = kwargs.get("conn", None)
    if conn is None:
        if self.pool is None:
            io.echo(f"mm.item.save.180: {self.pool=}", level="error")
            return False
        with database.connect(self.args, pool=self.pool) as conn:
            return _work(conn)
    else:
        return _work(conn)
```

**Key principles:**
- Always use `with database.connect()` context manager
- Pass `commit=False` to database operations to defer commit to context manager
- Let context manager handle commit on successful exit
- Let context manager handle connection return to pool
- Explicit `conn.commit()` before pool return causes "rolling back returned connection" warning

## Database

- **Table**: `murdermotel.item`
- **Primary Key**: `(name, serial)`

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `kind` | text | Item type ('weapon', 'boobytrap', 'component', 'defense', 'item') |
| `modulepath` | text | Custom module path |
| `name` | citext | Item name (part of PK) |
| `serial` | int | Serial number (part of PK, unique per name) |
| `title` | text | Display title |
| `state` | jsonb | Instance state (weapon stats, durability, etc.) |

## Item Kinds

| Kind | Description |
|------|-------------|
| `weapon` | Complete weapons (axes, pistols, etc.) — generated from `weapon_recipe` |
| `boobytrap` | Active traps |
| `component` | Weapon parts (blades, handles) — assembled into weapons |
| `defense` | Defensive items |
| `item` | Generic items |

## Weapon System

### `murdermotel.weapon_recipe`

Defines how weapons are built and distributed. Each recipe specifies the two required components, how many instances to generate (rarity control), shared messages, and default state.

| Column | Type | Description |
|--------|------|-------------|
| `name` | citext PK | Weapon name — 'axe', 'pistol', etc. |
| `title` | text | Display name for the weapon |
| `component1` | citext | First required component |
| `component2` | citext | Second required component |
| `count` | int | Number of instances to generate (default 6). Lower = rarer. 0 = disabled. |
| `usemessages` | text[] | Shared kill/attack messages for all instances |
| `state` | jsonb | Default state copied into each item instance at generation time |

### Recipe Defaults vs Instance State

Recipe `state` is **default values** copied into each item at generation time. Instance `state` in `murdermotel.item` can be modified independently (e.g., ammo consumed, durability lost).

```json
// axe — high damage melee weapon
{"damage_min": 15, "damage_max": 30, "type": "melee", "power": "high"}

// pistol — ranged weapon with limited ammo (set count=3 for rarity)
{"damage_min": 10, "damage_max": 20, "type": "ranged", "ammo": 6, "ammo_max": 6}

// chlorine — area-effect chemical weapon
{"damage_min": 5, "damage_max": 25, "type": "area", "radius": 1}

// fire — flame weapon
{"damage_min": 20, "damage_max": 40, "type": "burn", "area": false}

// acid — corrosive weapon
{"damage_min": 12, "damage_max": 35, "type": "corrosive", "uses": 3, "uses_max": 3}
```

### Weapon Mode

The `WEAPON_MODE` config in `lib.py` controls distribution:

| Mode | Behavior |
|------|----------|
| `components` | Distribute components only. Players assemble via `weapon_recipe` lookup in `Player.weapons()`. |
| `complete` | Distribute pre-built `kind='weapon'` items directly into rooms. Players pick them up without assembly. |
| `both` | Both: components distributed as normal, plus complete weapon instances placed in rooms. |

### Weapon Assembly (components mode)

When `WEAPON_MODE` is `'components'` or `'both'`, `Player.weapons()` queries `weapon_recipe` for the assembly list and checks if both required components are in the player's inventory. If so, the components are consumed and a virtual "weapon" is presented to the player (no `item` row created — it's an in-memory weapon constructed from components).

## Item Mapping

- **Table**: `murdermotel.map_item_room`
- **Columns**: `roomid`, `itemname`, `serial`
- **Table**: `murdermotel.map_item_player`
- **Columns**: `playermoniker`, `itemname`, `serial`