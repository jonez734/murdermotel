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
| `save` | `(mogrify=False, **kwargs)` | Save item to database |

## Database

- **Table**: `murdermotel.item`
- **Primary Key**: `name` (citext)

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `kind` | text | Item type ('weapon', 'boobytrap', 'component', 'defense') |
| `modulepath` | text | Custom module path |
| `name` | citext | Item name (PK) |
| `serial` | int | Serial number |
| `title` | text | Display title |
| `state` | jsonb | Item state |

## Item Kinds

| Kind | Description |
|------|-------------|
| `weapon` | Complete weapons (axes, pistols, etc) |
| `boobytrap` | Active traps |
| `component` | Weapon parts (blades, handles) |
| `defense` | Defensive items |

## Weapon Components

Items are combined to form complete weapons:

| Weapon | Component 1 | Component 2 |
|--------|--------------|-------------|
| `axe` | `axeblade` | `axehandle` |
| `pistol` | `pistol` | `bullets` |
| `chlorine` | `chlorinegas` | `gassprayer` |
| `fire` | `lighterfluid` | `flamethrower` |
| `acid` | `industrialacid` | `acidsprayer` |

## Item Mapping

- **Table**: `murdermotel.map_item_room`
- **Columns**: `roomid`, `itemname`, `serial`
- **Table**: `murdermotel.map_item_player`
- **Columns**: `playermoniker`, `itemname`, `serial`