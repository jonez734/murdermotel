# Murdermotel Bot NPCs - Specification

> **Implementation Status**: Core complete, integration testing in progress
> **Test Suite**: 39 tests passing in `test_bot.py`

---

## Overview

Add AI-controlled bot players ("NPCs without keyboards") that behave like real players - they move through rooms, collect items, and can be targeted by real players (and vice versa). This creates an assassin game mechanic where players hunt bots and are hunted by them.

---

## Implementation Notes

### Key Patterns

**Pool/Connection Handling** (critical):
```python
def some_function(args, **kwargs) -> ReturnType:
    def _work(conn):
        # ONLY use conn for DB operations
    
    conn = kwargs.get("conn")
    if conn is None:
        pool = kwargs.get("pool")
        if pool is None:
            io.echo("error", level="error")
            return error_value
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)
```

**Never use**:
- `pool=None` defaults in function parameters
- `args.pool` 
- `getattr(args, "pool", None)`

### Bugs Discovered & Fixed

1. **Pool handling bug**: Used `getattr(args, "pool", None)` → caused `'Connection' object has no attribute 'getconn'`
2. **item.py bug**: Query param was `dat = itemname` (bare string) → should be `dat = (itemname,)` (tuple)
3. **item.py column mismatch**: Test DB had `type`/`module` columns but code expected `kind`/`modulepath`
4. **bot.py dead player check**: Used `died=false` → should be `died is null` since column is bigint
5. **Player class missing attributes**: Added `target` and `targetedby` to FIELDS and `__init__`
6. **Python scoping**: Use `nonlocal` when assigning to variables from enclosing scope inside nested `_work` functions

---

## Constants

Define in `lib.py`:

```python
# Bot configuration
BOT_KILL_POINTS = 50           # Points awarded for killing a bot
BOT_MAX_COUNT = 20             # Maximum bots to prevent performance issues
BOT_COUNT_RATIO = 1            # Bots per real player
BOT_STARTING_MOVES = 60

# Bot behavior probabilities
BOT_PICKUP_CHANCE = 0.3        # 30% chance to pick up item in room
BOT_DROP_CHANCE = 0.2          # 20% chance to drop item if full
BOT_ATTACK_CHANCE = 0.4        # 40% chance to attack if target in room

# Bot modes (stored in npc.state->mode)
BOT_MODE_STATIC = "static"     # Stationary, only acts when encountered
BOT_MODE_SIMPLE = "simple"     # Random movement only
BOT_MODE_FULL = "full"         # Full simulation: move + items + hunt target
BOT_MODE_HYBRID = "hybrid"     # Default: all behaviors combined
```

---

## Database Schema

### Modify `murdermotel.npc` table

Add columns:

```sql
ALTER TABLE murdermotel.npc 
    ADD COLUMN IF NOT EXISTS is_bot boolean DEFAULT false,
    ADD COLUMN IF NOT EXISTS target text,
    ADD COLUMN IF NOT EXISTS targetedby text,
    ADD COLUMN IF NOT EXISTS is_alive boolean DEFAULT true;
```

The existing `state` JSONB column stores:
```json
{
  "mode": "hybrid",
  "items": ["axeblade", "axehandle"],
  "last_action": "2026-04-16T12:00:00Z"
}
```

### New table `murdermotel.npc_player_items`

Items carried by bot NPCs:

```sql
CREATE TABLE murdermotel.npc_player_items (
    npcmoniker text REFERENCES murdermotel.npc(name) ON DELETE CASCADE,
    itemname text REFERENCES murdermotel.item(name),
    PRIMARY KEY (npcmoniker, itemname)
);
```

---

## Bot Naming

### Generation Algorithm

Bot names constructed from prefix + suffix pools:

```python
BOT_PREFIXES = [
    "Silent", "Shadow", "Ghost", "Dark", "Creep",
    "Night", "Steel", "Iron", "Crimson", "Pale",
    "Wicked", "Vile", " Grim", "Haunted", "Obsidian"
]

BOT_SUFFIXES = [
    "Stalker", "Hunter", "Runner", "Walker", "Slayer",
    "Blade", "Fang", "Wraith", "Shade", "Reaper",
    "Viper", "Specter", "Chimera", "Grave", "Howler"
]
```

Format: `{Prefix}{Suffix}` (e.g., "GhostWalker", "SteelHunter")

### Uniqueness

- Generate name, check `murdermotel.npc` table for existing `name` where `is_bot=true`
- If collision, regenerate (max 10 attempts)
- Names persist globally across game sessions

---

## Bot Class

Located in `bot.py`, extends `Living` class.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | str | Unique bot moniker |
| `kind` | str | Always "bot" |
| `modulepath` | str | Always "bot" |
| `roomid` | int | Current location in playground |
| `moves` | int | Remaining moves this turn (default: 60) |
| `healthpoints` | int | Health (default: 35) |
| `target` | str | Moniker of entity bot is hunting |
| `targetedby` | str | Moniker of entity hunting bot |
| `is_alive` | bool | True unless killed |
| `items` | list[Item] | Carried items |
| `mode` | str | Behavior mode from constants |

### Methods

```python
def on_turn(self, args, room=None, **kwargs) -> bool:
    """Execute bot's turn based on mode."""
    
def _move_randomly(self, exits: dict) -> bool:
    """Pick random exit direction. Returns True if moved."""

def _handle_items(self, room) -> bool:
    """Pick up items (30% chance) or drop items (20% chance)."""

def _handle_combat(self, player, room) -> bool:
    """If target in room, attempt to kill."""
```

---

## Bot Modes & Behavior

### Mode Definitions

| Mode | Movement | Items | Combat | Percentage |
|------|----------|-------|--------|------------|
| `static` | None | None | Only when player enters room | Dynamic |
| `simple` | Random direction | None | Attack if target in room | Dynamic |
| `full` | Smart pathfinding | Pick/drop | Hunt target aggressively | Dynamic |
| `hybrid` | Random + smart | 30% pickup | Attack if has weapon | Dynamic |

### Dynamic Mode Distribution

Based on number of real players in game:

```python
def get_mode_distribution(player_count: int) -> dict:
    if player_count < 5:
        return {"hybrid": 0.6, "simple": 0.2, "static": 0.1, "full": 0.1}
    elif player_count <= 10:
        return {"hybrid": 0.3, "simple": 0.3, "static": 0.2, "full": 0.2}
    else:  # > 10
        return {"hybrid": 0.25, "simple": 0.25, "static": 0.25, "full": 0.25}
```

---

## Target Assignment

### Pool Definition

The pool of potential targets = **all living players + all living bots**

When a player or bot needs a target:
- Real players can target: other real players + all bots
- Bots can target: real players + other bots

### Weighted Selection

Experience-based weighting (all three factors):

```python
def get_experience_score(entity) -> int:
    """Calculate experience score for targeting weight."""
    kills = getattr(entity, 'bodycount', 0) or 0
    points = getattr(entity, 'points', 0) or 0
    turns = getattr(entity, 'turn', 0) or 0
    return (kills * 10) + points + (turns * 2)
```

Selection probability: higher experience → higher chance of being targeted

### Bidirectional Targeting

Every assignment is bidirectional:
- If Player A targets Bot X, then Bot X's `targetedby` = Player A
- If Bot Y targets Player B, then Player B's `targetedby` = Bot Y

### Single Player Edge Case

If only 1 real player in game:
- Player can only be assigned bots as targets
- Bots still target the single player (bidirectional player↔bot)
- Bot-on-bot targeting enabled

---

## Target Visibility

### Forward (Player → Target)
- **Visible**: Player can see who they're assigned to kill
- Display: "You are hunting: GhostHunter"

### Reverse (Target → Player)
- **Hidden**: Player cannot see who has them as target
- Display: "You are being hunted" (no name shown)

---

## Bot Persistence

### On Player Exit to Lobby
- Bots remain in database with `is_alive=true`
- All state preserved (roomid, items, target, mode)

### On Player Return to Game
1. Load player's `target` from database
2. Verify target exists and `is_alive=true`
3. **If target missing** (killed while player was away):
   - Find another living bot to assign
   - If no bots exist, generate new one(s) up to BOT_MAX_COUNT
   - Update player's `target` field

### Cleanup
- Dead bots (`is_alive=false`) remain until game ends
- When all players quit, dead bots can be cleaned up via maintenance

---

## Combat Mechanics

### Bot Attacks Player
- Similar to `RabidWolf.attack_player()`
- Player loses moves based on damage
- If player moves reach 0, player dies

### Player Attacks Bot
- Player uses weapon (same as wolf combat)
- Bot takes damage (healthpoints reduced)
- If bot health reaches 0: bot dies, player awarded BOT_KILL_POINTS
- Survivor gets reassigned new target

### Bot Attacks Bot
- Same mechanics as bot attacks player
- Killer bot gets new target assigned

### On Kill
1. Award points: Player kills bot → +BOT_KILL_POINTS
2. Mark victim: `is_alive=false`, remove from registry
3. Reassign: Find new target for survivor

---

## UI Display

### In Lobby
- Bots listed with `:robot:` prefix
- Show player's target: "You are hunting: GhostHunter"
- Hide reverse: "You are being hunted" (no name)

### In Room
- Bots appear: `:robot: GhostHunter is here.`
- If player is bot's target: "GhostHunter is looking for you!"

### Status Bar
- Show target name (forward only)

---

## Integration Points

### `startup.py`
- Add bot SQL migration to `_TABLES`

### `lib.py`
- Add bot constants
- Add helper: `get_all_huntable_entities(args, pool)` - returns list of living players + bots

### `bot.py` (NEW)
- Bot class
- generate_bot_name()
- generate_bots()
- assign_targets()
- load(), create(), save(), getitems()
- ensure_valid_target()

### `lobby.py`
- On `run`: load or generate bots
- Handle missing target edge case

### `room.py`
- Display bots in room description

### `play.py`
- Add bots to ObjectRegistry
- Process bot turns each cycle
- Handle kill resolution

---

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Player returns, target gone | Reassign to new living bot |
| All bots dead | Generate more (up to BOT_MAX_COUNT) |
| Single player | Player targets bots only |
| Bot name collision | Regenerate (max 10 attempts) |
| Bot in glowing sphere | Treat as normal room |

---

## File Changes Summary

| File | Action |
|------|--------|
| `data/sql/npc.sql` | Add columns: is_bot, target, targetedby, is_alive |
| `data/sql/npc_player_items.sql` | **NEW** - Items table for bots |
| `lib.py` | Add constants, helper functions |
| `bot.py` | **NEW** - Bot class, generation, AI, targeting |
| `lobby.py` | Load/assign bots, handle missing targets |
| `room.py` | Display bots in rooms |
| `play.py` | Process bot turns, handle kills |
| `startup.py` | Add SQL files to _TABLES |

---

## Testing Checklist

- [x] Bot generation creates correct number of bots
- [x] Bot names are unique globally
- [x] Mode distribution is correct based on player count
- [x] Targets assigned bidirectionally
- [x] Experience weighting affects target selection
- [x] Single player → bots only as targets
- [x] Target visible forward, hidden reverse
- [x] Bots persist when player exits to lobby
- [x] Missing target reassignment works
- [x] Bot kills award correct points
- [x] Dead bots removed from registry
- [ ] Bots display correctly in rooms (partially done via play.py)

---

## Files Modified/Created

### Created:
- `src/murdermotel/bot.py` - Bot class, generation, AI, targeting
- `src/murdermotel/test_bot.py` - 39 tests (all passing)
- `src/murdermotel/data/sql/npc_player_items.sql` - Bot items table

### Modified:
- `src/murdermotel/lib.py` - Added bot constants
- `src/murdermotel/player.py` - Added target/targetedby to FIELDS and __init__
- `src/murdermotel/lobby.py` - Generate bots on startup
- `src/murdermotel/play.py` - Register bots, assign targets, display in rooms
- `src/murdermotel/data/sql/npc.sql` - Added columns
- `src/murdermotel/data/sql/player.sql` - Added columns
- `src/murdermotel/item.py` - Fixed query param tuple, handle legacy columns