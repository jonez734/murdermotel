# Murder Motel Database Schema

## Overview

PostgreSQL schema for the Murder Motel game. Uses explicit joins instead of table inheritance for type modeling.

## Module Specifications

Detailed specifications for each game module:

| File | Description |
|------|-------------|
| [SPEC_room.md](SPEC_room.md) | Room module (locations, exits) |
| [SPEC_player.md](SPEC_player.md) | Player module (characters, inventory) |
| [SPEC_item.md](SPEC_item.md) | Item module (weapons, components, traps) |
| [SPEC_obj.md](SPEC_obj.md) | Base object classes and registry |
| [SPEC_npc.md](SPEC_npc.md) | NPC modules (RabidWolf, Thief) |

### Maintenance Modules (sysop-only)

| Module | Description |
|--------|-------------|
| `housekeeping` | Maintenance menu with Setup, Edit, Weapon List, Quit |
| `weaponlist` | Sysop-only tool showing components and recipe info |

The `weaponlist` module provides two options:
- **C** - Components: Lists all components with their room locations
- **R** - Recipes: Shows each weapon recipe with its two components and room numbers (or "unplaced" if not in any room)

## Tables

### Core Tables

| Table | Description |
|-------|-------------|
| `murdermotel.playground` | Game rooms/locations |
| `murdermotel.player` | Game players |
| `murdermotel.item` | Items (weapons, booby traps) |
| `murdermotel.npc` | NPCs (wolves, thieves) |

### Item Subtypes (via join)

| Table | Parent | Additional Columns |
|-------|--------|-------------------|
| `murdermotel.boobytrap` | `item` | `running`, `timer` |

### NPC Subtypes (via join)

| Table | Parent | Additional Columns |
|-------|--------|-------------------|
| `murdermotel.rabidwolf` | `npc` | `roomid`, `healthpoints` |
| `murdermotel.thief` | `npc` | `bag` (citext[]), `roomid`, `healthpoints` |

### Mapping Tables

| Table | Purpose |
|-------|---------|
| `murdermotel.map_item_player` | Items held by players |
| `murdermotel.map_item_room` | Items placed in rooms |
| `murdermotel.map_item_thief` | Items stolen by the thief |

### Weapon System

| Table | Purpose |
|-------|---------|
| `murdermotel.weapon_recipe` | Weapon definitions: name, components, count, defaults |

## Design Decisions

### Kind Column Pattern

Each parent table uses a `kind` column with CHECK constraint to enforce valid subtypes:

- `item.kind` ∈ {'weapon', 'boobytrap', 'component', 'defense', 'item'}
- `npc.kind` ∈ {'wolf', 'thief'}

### Weapon Mode

The `WEAPON_MODE` config in `lib.py` controls weapon distribution:

| Mode | Behavior |
|------|----------|
| `components` | Distribute components only. Players assemble weapons via `weapon_recipe`. |
| `complete` | Distribute pre-built `kind='weapon'` items directly into rooms. |
| `both` | Both: components + complete weapons placed in rooms. |

### Instance State

Each weapon instance in `murdermotel.item` has a `state` JSONB column that can diverge from the recipe defaults. The `weapon_recipe.state` column provides default values copied into each instance at generation time.

## Save Pattern

All `save()` methods follow a consistent pattern for transaction management:

1. `_work(conn)` nested function performs DB operations (upserts, inserts, updates)
2. If external `conn` provided: call `_work(conn)` and commit, return result
3. If only `pool` provided: acquire connection, call `_work(conn)`, commit, close
4. All save methods use `commit=False` on upsert calls to defer commit until outer scope

This pattern ensures proper resource cleanup and transaction handling.

## Loading Order

```
schema.sql
  → player.sql
  → playground.sql
  → item.sql
    → weapon_recipe.sql (weapon.sql)
    → boobytrap.sql
  → npc.sql
    → wolf.sql
    → thief.sql
```