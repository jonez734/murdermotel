# Living Attack System - Wandering NPCs

> **Implementation Status**: Implemented
> **Target NPC**: rabidwolf (proof of concept)

---

## Overview

Implement a "living" attack system where NPCs like the rabidwolf can wander between rooms, creating dynamic encounters. The player may encounter the wolf unexpectedly as it moves through the motel.

---

## RabidWolf Wandering Implementation

### Changes to `rabidwolf.py`

1. **Add `_move_randomly()` method to `RabidWolf` class** (around line 36):
   ```python
   def _move_randomly(self, args, **kwargs) -> bool:
       """Pick random exit direction from current room."""
       room = libroom.load(args, self.roomid, **kwargs)
       if not room or not hasattr(room, "exits") or not room.exits:
           return False
       exits = room.exits
       valid_exits = [d for d, target in exits.items() if target is not None]
       if not valid_exits:
           return False
       direction = random.choice(valid_exits)
       self.roomid = exits[direction]
       io.echo(f"The wolf wanders {direction}.", level="debug")
       return True
   ```

2. **Add wandering to `on_turn()` method** (around line 48):
   - 30% chance to wander per turn
   - Only wander if player NOT in same room (don't flee from combat)
   - After moving, check if player in adjacent room → display "You hear howling nearby."

3. **Add same logic to module-level `turn()` function** (around line 307)
   - Both `on_turn()` and `turn()` are called from game loop
   - Keep wandering logic in sync

4. **Ensure roomid persists**
   - Existing `self.save()` calls handle persistence

### Key Behavior
- Wolf wanders 30% of turns when not in combat
- Player notification: "You hear howling nearby" when wolf in adjacent room
- Wolf avoids room 0 (death) and room 1 (lobby) - uses spawn range 10 to count-10

---

## Future Features (Deferred)

1. **Hunting behavior**: Wolf preferentially moves toward player in adjacent rooms
2. **Room boundaries**: Define safe zones where NPCs cannot enter
3. **Other NPCs**: Apply same wandering system to thief and other attacking NPCs
