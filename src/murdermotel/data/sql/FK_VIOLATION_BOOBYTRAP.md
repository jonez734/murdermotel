# FK Violation Bug: boobytrap table

## Error

```
bbsengine6.database.upsert.300: insert or update on table "boobytrap" violates foreign key constraint "fk_boobytrap_item"

DETAIL:  Key (name, serial)=(boobytrap, 1) is not present in table "item".
```

## Root Cause

The `boobytrap` table has a foreign key constraint to the `item` table:

```sql
-- boobytrap.sql
constraint fk_boobytrap_item foreign key (name, serial) 
  references murdermotel.item(name, serial) on update cascade on delete cascade,
```

The `boobytrap` table uses `serial=1` by default, so it requires an item record with `(name='boobytrap', serial=1)` to exist **before** inserting into `boobytrap`.

The code was calling `database.upsert()` directly on the `boobytrap` table without first creating the corresponding record in the `item` table.

## Fix

### Files Modified

1. **boobytrap.py** - 3 locations:
   - `create()` function (line ~258): Now upserts to `item` table first, then to `boobytrap`
   - `save()` function (line ~206): Now upserts to `item` table first, then updates `boobytrap`
   - `BoobyTrap.save()` method (line ~108): Now upserts to `item` table first, then updates `boobytrap`

2. **maintenance.py** - Added boobytrap item creation during weapons setup:
   - After creating weapon components, now also creates the boobytrap item entry with `serial=1`

### Pattern Applied

```python
# First, ensure item record exists
item_rec = {
    "name": BOOBYTRAP_NAME,
    "serial": 1,
    "kind": "boobytrap",
    "modulepath": "boobytrap",
    "title": "Booby Trap",
}
database.upsert(args, f"{libmm.SCHEMA}.item", item_rec, ...)

# Then, operate on boobytrap
database.upsert(args, f"{libmm.SCHEMA}.boobytrap", rec, ...)
```

## Related Tables

The `weapon` table has similar FK constraints to `item`:

```sql
-- weapon.sql
constraint fk_weapon_component1 foreign key (component1, component1_serial) references murdermotel.item(name, serial),
constraint fk_weapon_component2 foreign key (component2, component2_serial) references murdermotel.item(name, serial),
constraint fk_weapon_item foreign key (name, serial) references murdermotel.item(name, serial)
```

Currently, the `weapon` table is not being used in code (no CRUD operations found), so this was not an issue. If weapon CRUD is implemented in the future, the same pattern should be applied.