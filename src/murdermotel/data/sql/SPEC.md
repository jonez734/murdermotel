# Murder Motel Database Schema

## Overview

PostgreSQL schema for the Murder Motel game. Uses explicit joins instead of table inheritance for type modeling.

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
|-------|--------|---------------------|
| `murdermotel.weapon` | `item` | `component1`, `component2` |
| `murdermotel.boobytrap` | `item` | `running`, `timer` |

### NPC Subtypes (via join)

| Table | Parent | Additional Columns |
|-------|--------|---------------------|
| `murdermotel.rabidwolf` | `npc` | `roomid`, `healthpoints` |
| `murdermotel.thief` | `npc` | `bag` (citext[]), `roomid`, `healthpoints` |

### Mapping Tables

| Table | Purpose |
|-------|---------|
| `murdermotel.map_item_player` | Items held by players |
| `murdermotel.map_item_room` | Items placed in rooms |
| `murdermotel.map_item_thief` | Items stolen by the thief |
| `murdermotel.component` | Weapon components |

## Design Decisions

### Kind Column Pattern

Each parent table uses a `kind` column with CHECK constraint to enforce valid subtypes:

- `item.kind` ∈ {'weapon', 'boobytrap'}
- `npc.kind` ∈ {'wolf', 'thief'}

### Foreign Key Pattern

Child tables use their parent's primary key as both their PK and FK:

```sql
-- Example: weapon table
name citext unique not null,
constraint fk_weapon_item foreign key (name) references murdermotel.item(name) ...
```

This enforces the "is-a" relationship at the database level and enables cascading deletes.

## Loading Order

```
schema.sql
  → player.sql
  → playground.sql
  → item.sql
    → weapon.sql
    → boobytrap.sql
  → npc.sql
    → wolf.sql
    → thief.sql
```

Note: Parent tables must be loaded before child tables due to FK constraints.
