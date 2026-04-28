# SPEC_obj.md - Murder Motel Object Module

## Overview

Base object classes and registry for Murder Motel game objects. Provides common functionality for NPCs, items, and other game entities.

## ObjectRegistry Class

Registry for active game objects (NPCs, items) that need turn processing.

```python
class ObjectRegistry:
    _objects: list
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `register` | `(obj) -> None` | Register object |
| `unregister` | `(obj) -> None` | Unregister object |
| `get_by_room` | `(roomid: int) -> list` | Get objects in room |
| `all` | `() -> list` | Get all objects |
| `clear` | `() -> None` | Clear registry |
| `get_by_name` | `(name: str)` | Find object by name |

## Registry Instance

Global registry instance:

```python
registry = ObjectRegistry()
```

## Obj Class

Base object class for all game entities.

```python
class Obj:
    modulepath = None
    args: argparse.Namespace
    table: str
    fields: tuple
    classname: str
    name: str | None
    roomid: int | None
    isdirty: bool
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `on_turn` | `(args, room=None, **kwargs) -> Optional[bool]` | Handle turn processing |
| `short` | `() -> str` | Get short description |
| `load` | `(name, **kwargs) -> bool` | Load from database |
| `save` | `(**kwargs) -> bool` | Save to database |
| `move` | `(args, roomid: int, **kwargs) -> bool` | Move to room |

## Living Class

Base class for living entities (NPCs).

```python
class Living(Obj):
    roomid: int | None
```

Inherits from `Obj`.

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `short` | `() -> str` | Get short description |

## Module Dependencies

- `bbsengine6.database`
- `bbsengine6.io`

## Database Interaction

Both `Obj.load()` and `Obj.save()` support:
- `conn` - existing database connection
- `pool` - connection pool (creates connection if needed)