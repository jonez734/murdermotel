# SPEC_room.md - Murder Motel Room Module

## Overview

Room module for the Murder Motel game. Manages game locations/exits and provides room validation.

## Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `init` | `(args, obj=None, room=None, **kwargs) -> bool` | Module initialization |
| `access` | `(args, op, **kwargs) -> bool` | Check if operation is permitted |
| `buildargs` | `(args, obj=None, room=None, **kwargs)` | Build command-line arguments |
| `main` | `(args, **kwargs) -> bool` | Main entry point |
| `load` | `(args, roomid, **kwargs)` | Load room by ID or shortname |
| `getitems` | `(args, roomid, **kwargs) -> list` | Get items in room |
| `getcount` | `(args, **kwargs)` | Get total room count |
| `build` | `(args, rec: dict, **kwargs) -> Room` | Build Room from record |
| `is_valid` | `(args, roomid, **kwargs) -> bool` | Validate room exists |

## Room Class

```python
class Room:
    args: argparse.Namespace
    modulepath: str | None
    shortname: str | None
    id: int | None
    title: str | None
    description: str | None
    items: list
    exits: dict
    table: str
    pool: object
    north: int | None
    south: int | None
    east: int | None
    west: int | None
    up: int | None
    down: int | None
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `on_turn` | `(args, room=None, **kwargs) -> bool` | Handle turn processing |
| `short` | `() -> str` | Get short room description |
| `buildrec` | `()` | Build database record |
| `finditem` | `(shortname)` | Find item by name |
| `save` | `(mogrify=False, commit=True, **kwargs)` | Save room to database (commit=False defers to outer transaction) |

## Database

- **Table**: `murdermotel.playground`
- **Primary Key**: `id`
- **Fields**: `id`, `modulepath`, `description`, `title`, `shortname`, `north`, `south`, `east`, `west`, `up`, `down`

## Exits

Standard compass directions + vertical:
- `north`, `south`, `east`, `west`, `up`, `down`

Each exit references another room's `id`.