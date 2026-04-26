# Trap Rooms Specification

## Overview

Trap rooms are special game rooms where players are trapped and must meet certain conditions to escape. The trap framework provides a generic base class that can be extended for different trap types.

## Architecture

### Core Files

| File | Purpose |
|------|---------|
| `traproom.py` | Generic trap framework (TrapRoom class and functions) |
| `inside_glowing_sphere.py` | Example trap room extending TrapRoom |
| `play.py` | Game loop, handles trap detection and escape |
| `room.py` | Base Room class (TrapRoom inherits from this) |

### Class Hierarchy

```
room.Room (bbsengine6)
    ↑
    traproom.TrapRoom
            ↑
            inside_glowing_sphere.GlowingSphereTrap
```

### Flow

```
1. Player presses direction (N/S/E/W/U/D)
2. play.py: _handle_trap() checks if room is a trap:
   - Reads room.TRAP_EXITS (None = all directions trigger trap)
   - If direction triggers trap:
     a. Calls room.on_turn() (runs attempt())
     b. If attempt() returns False:
        - Shows room.TRAP_MESSAGE
        - Player stays trapped
     c. If attempt() returns True:
        - Tries success() → solved() → win() (first to return valid room ID)
        - Moves player to returned room ID
3. If direction doesn't trigger trap:
   - Move via normal exit
```

## TrapRoom Class

### Configuration (Class Attributes)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `attempts_allowed` | int | 5 | Number of tries before escape allowed |
| `trap_message` | str | "You are trapped! Try again..." | Message shown when still trapped |
| `trap_exits` | tuple | None | Directions that trigger trap (None = all) |
| `escape_min` | int | 10 | Minimum escape room ID |
| `escape_max` | int | None | Maximum escape room ID (None = getcount() - 10) |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `on_turn()` | bool | Runs attempt logic, called by game loop |
| `attempt()` | bool | Returns True when attempts >= attempts_allowed |
| `success()` | int | Returns random room ID for escape |
| `solved()` | int | Alias for success() - override for custom behavior |
| `win()` | int | Alias for success() - override for custom behavior |
| `reset(moniker)` | None | Reset counter for specific player |

### Class Example

```python
from . import traproom as libtraproom

class MyTrap(libtraproom.TrapRoom):
    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self.attempts_allowed = 3
        self.trap_message = "Custom trap message!"
    
    def success(self, args, **kwargs) -> int:
        return 42  # Fixed escape room
```

## Functional API (Alternative)

For rooms that just need to alias functions without creating a class:

### Module-Level Functions

```python
def attempt(args, **kwargs) -> bool:
    """Returns True when player can escape (tracks attempts counter)."""

def success(args, **kwargs) -> int:
    """Returns random room ID for escape."""

def solved(args, **kwargs) -> int:
    """Alternative success - for puzzle/special completions."""

def win(args, **kwargs) -> int:
    """Alternative success - for game wins."""

def reset(args, moniker: str) -> None:
    """Reset counter for a specific player."""
```

### Required Module Attributes

| Variable | Type | Description |
|----------|------|-------------|
| `TRAP_EXITS` | tuple | Directions that trigger trap (None = all) |
| `ATTEMPTS_ALLOWED` | int | Number of tries before escape (for standalone functions) |

## Creating a New Trap Room (Two Ways)

### Option 1: Class-Based (Recommended)

```python
# my_trap.py
from . import traproom as libtraproom

class MyTrap(libtraproom.TrapRoom):
    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self.attempts_allowed = 3
        self.trap_message = "The door is locked! Try again..."

# Import all functions - call instance methods
init = libtraproom.init
access = libtraproom.access
buildargs = libtraproom.buildargs
main = libtraproom.main
turn = libtraproom.turn
attempt = libtraproom.attempt
success = libtraproom.success
solved = libtraproom.solved
win = libtraproom.win
reset = libtraproom.reset
```

### Option 2: Functional-Only

```python
# simple_trap.py
# Just customize config - uses traproom defaults

from . import traproom as libtraproom

ATTEMPTS_ALLOWED = 3
TRAP_MESSAGE = "The wall pulses..."

# Use all functions from traproom
init = libtraproom.init
access = libtraproom.access
buildargs = libtraproom.buildargs
main = libtraproom.main
turn = libtraproom.turn
attempt = libtraproom.attempt
success = libtraproom.success
solved = libtraproom.solved
win = libtraproom.win
reset = libtraproom.reset
```

## Custom Escape Example (Puzzle Trap)

```python
# puzzle_trap.py
from . import traproom as libtraproom

class PuzzleTrap(libtraproom.TrapRoom):
    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self.attempts_allowed = 3
        self.trap_message = "Wrong answer!"

_correct = {}  # {moniker: True}

    def attempt(self, args, **kwargs) -> bool:
        """Check if player already solved."""
        player = kwargs.get("player")
        if not player:
            return True
        return _correct.get(player.moniker, False)

    def solved(self, args, **kwargs) -> int:
        """Mark as solved and return escape room."""
        player = kwargs.get("player")
        if player:
            _correct[player.moniker] = True
        return self.success(args, **kwargs)

# Aliases
init = libtraproom.init
access = libtraproom.access
buildargs = libtraproom.buildargs
main = libtraproom.main
turn = libtraproom.turn  # Calls instance on_turn which calls attempt
reset = libtraproom.reset
```

## Game Configuration

### Registering Trap Rooms

Add trap rooms to `_ROOM_MODULEPATHS` in `startup.py`:

```python
_ROOM_MODULEPATHS = {
    128: "inside_glowing_sphere",
    200: "my_trap",  # Add your trap room
}
```

### Database

No additional schema needed - uses standard `playground` table.

## Library Functions (lib.py)

The runmodule operations are defined in `lib.py`:

| Operation | Stub | Description |
|-----------|------|-------------|
| `attempt` | `_stub_attempt` | Check if escape is allowed |
| `success` | `_stub_success` | Get escape room ID |
| `solved` | `_stub_success` | Alternative escape (puzzles) |
| `win` | `_stub_success` | Alternative escape (wins) |
| `turn` | `_stub_turn` | Backward compatibility |

## Internal Details

### Counter Storage

Attempts are stored in module-level dict:

```python
_counter = {}  # {moniker: turn_count}
```

Call `reset(moniker)` when player leaves the trap to clear their counter.

### Signature Validation

The library uses bbsengine6's signature validation. For trap operations (attempt, success, solved, win), the library bypasses strict signature checking because trap rooms often alias functions from traproom.py which have different signatures than the expected stub.