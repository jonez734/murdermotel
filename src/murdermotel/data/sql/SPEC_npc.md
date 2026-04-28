# SPEC_npc.md - Murder Motel NPC Modules

## Overview

NPC modules for the Murder Motel game. Includes RabidWolf and Thief enemy types.

- **RabidWolf**: `rabidwolf.py`
- **Thief**: `thief.py`

## RabidWolf

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `WOLF_NAME` | `"rabidwolf"` | NPC type identifier |
| `WOLF_HEALTH` | `35` | Starting health points |
| `WOLF_AUTO_ATTACK_CHANCE` | `6` | Auto-attack probability (1-10) |
| `WOLF_WANDER_CHANCE` | `3` | Wander probability (1-10) |

### RabidWolf Class

```python
class RabidWolf(Living):
    name: str
    healthpoints: int
    conn: object
    pool: object
    roomid: int | None
    modulepath: str | None
```

Inherits from `Living` (which inherits from `Obj`).

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `short` | `() -> str` | Get short description (`:wolf: rabid wolf`) |
| `buildrec` | `(**kwargs)` | Build database record |
| `_move_randomly` | `(args, **kwargs) -> bool` | Move to random adjacent room |
| `_is_player_adjacent` | `(args, player, **kwargs) -> bool` | Check if player nearby |
| `on_turn` | `(args, room=None, **kwargs) -> bool` | Handle turn processing |
| `save` | `(**kwargs) -> bool` | Save to database |

### Behavior

- **Wander**: Random chance to move to adjacent room each turn
- **Auto-Attack**: Attacks player if ignored or if player is nearby
- **Damage**: 1d10 + 10 moves damage per attack

### Database

- **Table**: `murdermotel.rabidwolf`
- **Primary Key**: `name` (FK to `murdermotel.npc`)

| Field | Type | Description |
|-------|------|-------------|
| `name` | text | NPC name (PK, FK) |
| `roomid` | int | Current room |
| `healthpoints` | int | Health remaining |

---

## Thief

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `THIEF_NAME` | `"thief"` | NPC type identifier |
| `THIEF_HEALTH` | `35` | Starting health points |

### Thief Class

```python
class Thief(Living):
    name: str
    bag: list
    healthpoints: int
    conn: object
    pool: object
    roomid: int | None
    items: list
    modulepath: str | None
```

Inherits from `Living` (which inherits from `Obj`).

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `short` | `() -> str` | Get short description (`:supervillian: Thief`) |
| `buildrec` | `(**kwargs)` | Build database record |
| `on_turn` | `(args, room=None, **kwargs) -> bool` | Handle turn processing |
| `steal` | `(args, player, **kwargs) -> bool` | Steal item from player |
| `save` | `(**kwargs) -> bool` | Save to database |

### Behavior

- **Steal**: Attempts to steal items from player inventory
- **Item Transfer**: Stolen items go into thief's bag

### Database

- **Table**: `murdermotel.thief`
- **Primary Key**: `name` (FK to `murdermotel.npc`)

| Field | Type | Description |
|-------|------|-------------|
| `name` | text | NPC name (PK, FK) |
| `bag` | text[] | Stolen items |
| `roomid` | int | Current room |
| `healthpoints` | int | Health remaining |

### Item Mapping

- **Table**: `murdermotel.map_item_thief`
- **Columns**: `thiefname`, `itemname`, `serial`

---

## NPC Base (via join)

Both NPC types join to the parent table:

- **Table**: `murdermotel.npc`
- **Primary Key**: `name` (citext)

| Field | Type | Description |
|-------|------|-------------|
| `name` | citext | NPC name (PK) |
| `kind` | text | NPC type ('wolf', 'thief') |

### Kind Constraints

| Kind | NPC Type |
|------|---------|
| `wolf` | RabidWolf |
| `thief` | Thief |