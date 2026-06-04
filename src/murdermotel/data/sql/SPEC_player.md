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
| `inputmoniker` | `(prompt, oldvalue, args, verify=None, **kwargs)` | Input player name with verification |
| `create` | `(args, playermoniker, **kwargs)` | Create new player |

## CONN_POOL_PATTERN

All database save/load methods use the standard bbsengine6 CONN_POOL_PATTERN:

```python
def save(self, **kwargs):
    def _work(conn):
        # Database operations with conn, commit=False
    
    conn = kwargs.get("conn", None)
    if conn is None:
        if self.pool is None:
            io.echo(f"mm.player.save.120: {self.pool=}", level="error")
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
- **Never** call `conn.commit()` explicitly - causes INTRANS rollback warning

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
| `save` | `(**kwargs)` | Save player to database (uses CONN_POOL_PATTERN: context manager handles commit) |
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