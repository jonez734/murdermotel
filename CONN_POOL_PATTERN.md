# Database Connection Pool Pattern

This documents the proper pattern for database connections in Murder Motel.

## Required Pattern for `.save()` Methods

All save methods in classes (Player, Room, Item, Thief, etc.) must follow this pattern:

```python
def save(self, mogrify=False, **kwargs):
    def _work(conn):
        # Database operations here
        # Use conn=conn for all database.* calls
        return True

    conn = kwargs.get("conn", None)
    if conn is None:
        if self.pool is None:
            io.echo(f"{self.classname}.save.100: pool is None", level="error")
            return False
        with database.connect(self.args, pool=self.pool) as conn:
            result = _work(conn)
            conn.commit()
            return result
    else:
        return _work(conn)
```

## Key Points

1. **Accept `**kwargs`** - allows caller to pass existing conn
2. **Check conn first**: `conn = kwargs.get("conn", None)`
3. **Check pool second**: if conn is None, check self.pool
4. **Fail if both None**: log error and return False
5. **Use nested `_work(conn)`**: keeps connection handling clean
6. **Pass `conn=conn`**: to all database.* function calls
7. **Commit in context**: after _work() completes

## Use upsert Instead of Update+Insert

Prefer `database.upsert()` over separate update/insert for atomic saves:

```python
database.upsert(
    args,
    "schema.table",
    {"id": self.id, "name": self.name},
    conflict_columns=["id"],  # unique constraint columns
    conn=conn,
)
```

## Files Following This Pattern

- `player.py` - Player.save()
- `obj.py` - Obj.save()
- `thief.py` - Thief.save()
- `rabidwolf.py` - RabidWolf.save()
- `bot.py` - Bot.save()

## Files Fixed To Follow This Pattern

- `room.py` - Room.save() [fixed 2026-04-20]
- `item.py` - Item.save() [fixed 2026-04-20]