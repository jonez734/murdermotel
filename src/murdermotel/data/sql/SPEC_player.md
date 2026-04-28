# SPEC_player.md - Murder Motel Player Module

## Overview

Player module for the Murder Motel game. Manages player characters, inventory, and game state.

## Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `access` | `(args, op, **kwargs) -> bool` | Check if operation is permitted |
| `init` | `(args, obj=None, room=None, **kwargs) -> bool` | Module initialization |
| `buildargs` | `(args, obj=None, room=None, **kwargs)` | Build command-line arguments |
| `main` | `(args, **kwargs) -> bool` | Main entry point |
| `turn` | `(args, **kwargs) -> bool` | Handle turn processing |
| `load` | `(args, moniker, **kwargs)` | Load player by moniker |
| `exists` | `(args, moniker, **kwargs) -> bool` | Check if player exists |
| `count` | `(args, membermoniker: str, **kwargs) -> int` | Count players by member |
| `getitems` | `(args, playermoniker, **kwargs) -> list` | Get player's items |
| `build` | `(args, rec: dict, **kwargs) -> Player` | Build Player from record |
| `inputmoniker` | `(prompt, oldvalue, args, **kwargs)` | Input player name with verification |
| `create` | `(args, playermoniker, **kwargs)` | Create new player |

## Player Class

```python
class Player:
    args: argparse.Namespace
    roomid: int | None
    died: int | None
    modulepath: str | None
    moniker: str
    turn: int
    moves: int
    datelastplayed: datetime.datetime
    items: list
    isdirty: bool
    points: int
    bodycount: int
    membermoniker: str | None
    pool: object
    conn: object
    exits: dict
    datecreated: datetime.datetime | None
    target: str | None
    targetedby: str | None
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `on_turn` | `(args, room=None, **kwargs)` | Handle turn processing |
| `short` | `() -> str` | Get short player description |
| `buildrec` | `(kwargs)` | Build database record |
| `weapons` | `(items=None)` | Find complete weapons from components |
| `finditem` | `(shortname)` | Find item by name |
| `save` | `(**kwargs)` | Save player to database |
| `info` | `()` | Display player info |
| `getitems` | `()` | Get player's items with weapons |

## Database

- **Table**: `murdermotel.player`
- **Primary Key**: `moniker` (citext)

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `moniker` | citext | Player name (PK) |
| `roomid` | int | Current room |
| `turn` | int | Current turn (day) |
| `moves` | int | Moves remaining |
| `bodycount` | int | NPCs killed |
| `points` | int | Score |
| `died` | int | Death timestamp |
| `modulepath` | text | Custom module |
| `membermoniker` | citext | BBS member |
| `datelastplayed` | timestamptz | Last played |
| `datecreated` | timestamptz | Account created |
| `target` | text | Current target |
| `targetedby` | text | Who targeted player |

## Item Mapping

- **Table**: `murdermotel.map_item_player`
- **Columns**: `playermoniker`, `itemname`, `serial`

## CompletePlayerName Class

Shell completion for player names.

```python
class completePlayerName:
    args: argparse.Namespace
    matches: list
    debug: bool
    pool: object
```

## Verification Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `verifyPlayerNameFound` | `(args, moniker: str, **kwargs) -> bool` | Verify moniker exists |
| `verifyPlayerNameNotFound` | `(args, moniker: str, **kwargs) -> bool` | Verify moniker available |