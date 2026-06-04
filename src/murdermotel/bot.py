# bot.py
# AI-controlled bot players for murdermotel

import argparse
import random
from typing import Any, Optional

from bbsengine6 import database, io
from bbsengine6.io import fatal_on_db_error

from . import lib as libmm
from . import room as libroom
from . import item as libitem
from .obj import Living, registry

BOT_MODE_STATIC = libmm.BOT_MODE_STATIC
BOT_MODE_SIMPLE = libmm.BOT_MODE_SIMPLE
BOT_MODE_FULL = libmm.BOT_MODE_FULL
BOT_MODE_HYBRID = libmm.BOT_MODE_HYBRID


BOT_PREFIXES = [
    "Silent",
    "Shadow",
    "Ghost",
    "Dark",
    "Creep",
    "Night",
    "Steel",
    "Iron",
    "Crimson",
    "Pale",
    "Wicked",
    "Vile",
    "Grim",
    "Haunted",
    "Obsidian",
    "Azure",
    "Cobalt",
    "Ebon",
    "Frost",
    "Onyx",
    "Ruby",
    "Silver",
    "Golden",
    "Emerald",
    "Violet",
]

BOT_SUFFIXES = [
    "Stalker",
    "Hunter",
    "Runner",
    "Walker",
    "Slayer",
    "Blade",
    "Fang",
    "Wraith",
    "Shade",
    "Reaper",
    "Viper",
    "Specter",
    "Chimera",
    "Grave",
    "Howler",
    "Phoenix",
    "Dragon",
    "Wolf",
    "Bear",
    "Fox",
    "Raven",
    "Tiger",
    "Panther",
    "Shadow",
    "Storm",
]


def generate_bot_name() -> str:
    """Generate a unique bot name from prefix + suffix pools."""
    prefix = random.choice(BOT_PREFIXES)
    suffix = random.choice(BOT_SUFFIXES)
    return f"{prefix}{suffix}"


def get_bot_name_unique(args, **kwargs) -> str:
    """Generate a unique bot name that doesn't exist in database."""
    for _ in range(10):
        name = generate_bot_name()
        if not exists(args, name, **kwargs):
            return name
    raise ValueError("Failed to generate unique bot name after 10 attempts")


def get_mode_distribution(player_count: int) -> dict:
    """Return mode distribution based on player count."""
    if player_count < 5:
        return {"hybrid": 0.6, "simple": 0.2, "static": 0.1, "full": 0.1}
    elif player_count <= 10:
        return {"hybrid": 0.3, "simple": 0.3, "static": 0.2, "full": 0.2}
    else:
        return {"hybrid": 0.25, "simple": 0.25, "static": 0.25, "full": 0.25}


def select_mode_by_distribution(player_count: int) -> str:
    """Select a mode based on distribution."""
    dist = get_mode_distribution(player_count)
    modes = list(dist.keys())
    weights = list(dist.values())
    return random.choices(modes, weights=weights, k=1)[0]


def get_experience_score(entity: Any) -> int:
    """Calculate experience score for targeting weight."""
    kills = getattr(entity, "bodycount", 0) or 0
    points = getattr(entity, "points", 0) or 0
    turns = getattr(entity, "turn", 0) or 0
    return (kills * 10) + points + (turns * 2)


def weighted_select(entities: list) -> Any:
    """Select an entity weighted by experience score."""
    if not entities:
        return None
    scores = [get_experience_score(e) for e in entities]
    total = sum(scores)
    if total == 0:
        return random.choice(entities)
    weights = [s / total for s in scores]
    return random.choices(entities, weights=weights, k=1)[0]


class Bot(Living):
    roomid: Optional[int] = None

    def __init__(self, args, **kwargs):
        super().__init__(args)
        self.name = kwargs.get("name", "bot")
        self.kind = "bot"
        self.modulepath = "bot"
        self.roomid = kwargs.get("roomid")
        if self.roomid is None:
            room_count = libroom.getcount(args, **kwargs)
            self.roomid = random.randint(10, room_count - 10) if room_count > 20 else 10
        self.moves = kwargs.get("moves", libmm.BOT_STARTING_MOVES)
        self.healthpoints = kwargs.get("healthpoints", 35)
        self.target = kwargs.get("target", None)
        self.targetedby = kwargs.get("targetedby", None)
        self.is_alive = kwargs.get("is_alive", True)
        self.mode = kwargs.get("mode", libmm.BOT_MODE_HYBRID)
        self.items = kwargs.get("items", [])
        self.conn = kwargs.get("conn")
        self.pool = kwargs.get("pool")
        if kwargs.get("register", True):
            registry.register(self)

    def short(self) -> str:
        return f":robot: {self.name}"

    def buildrec(self, **kwargs):
        rec = {}
        rec["name"] = self.name
        rec["kind"] = self.kind
        rec["modulepath"] = self.modulepath
        rec["roomid"] = self.roomid
        rec["is_bot"] = True
        rec["target"] = self.target
        rec["targetedby"] = self.targetedby
        rec["is_alive"] = self.is_alive
        state = {"mode": self.mode}
        rec["state"] = state
        return rec

    def on_turn(self, args, room=None, **kwargs) -> bool:
        """Execute bot's turn based on mode."""
        if not self.is_alive:
            return True

        if self.mode in (libmm.BOT_MODE_SIMPLE, libmm.BOT_MODE_HYBRID):
            self._move_randomly(args, room, **kwargs)
        if self.mode in (libmm.BOT_MODE_FULL, libmm.BOT_MODE_HYBRID):
            self._handle_items(room)
        if self.mode in (
            libmm.BOT_MODE_STATIC,
            libmm.BOT_MODE_SIMPLE,
            libmm.BOT_MODE_FULL,
            libmm.BOT_MODE_HYBRID,
        ):
            self._handle_combat(args, room, **kwargs)

        pool = kwargs.get("pool", None)
        conn = kwargs.get("conn", None)
        if conn is None and pool is not None:
            with database.connect(self.args, pool=pool) as conn:
                room.save(conn=conn)
                self.save(conn=conn)
        else:
            if self.pool:
                self.save(conn=conn) if conn else self.save()
        return True

    def _move_randomly(self, args, room, **kwargs) -> bool:
        """Pick random exit direction."""
        if not room or not hasattr(room, "exits") or not room.exits:
            return False
        exits = room.exits
        valid_exits = [d for d, target in exits.items() if target is not None]
        if not valid_exits:
            return False
        direction = random.choice(valid_exits)
        target_roomid = exits[direction]
        return self.move(args, roomid=target_roomid, **kwargs)

    def _handle_items(self, room) -> bool:
        """Pick up items (30% chance) or drop items (20% chance)."""
        if not room or not hasattr(room, "items"):
            return False

        if random.random() < libmm.BOT_PICKUP_CHANCE:
            if room.items and len(self.items) < libmm.MAXITEMSPERPLAYER:
                item = random.choice(room.items)
                self.items.append(item)
                room.items.remove(item)

        if random.random() < libmm.BOT_DROP_CHANCE:
            if self.items:
                item = random.choice(self.items)
                self.items.remove(item)
                room.items.append(item)
        return True

    def _handle_combat(self, args, room, **kwargs) -> bool:
        """If target in room, attempt to kill."""
        if not room:
            return False

        if random.random() > libmm.BOT_ATTACK_CHANCE:
            return False

        target_name = self.target
        if not target_name:
            return False

        in_room = False
        if hasattr(room, "players"):
            for p in room.players:
                if getattr(p, "moniker", None) == target_name:
                    in_room = True
                    break

        if not in_room and self.roomid is not None:
            for obj in registry.get_by_room(self.roomid):
                if isinstance(obj, Bot) and obj.name == target_name:
                    in_room = True
                    break

        if in_room and self.items:
            pass

        return True

    def save(self, **kwargs) -> bool:
        def _work(conn):
            rec = self.buildrec()
            if not database.upsert(
                self.args,
                f"{libmm.SCHEMA}.npc",
                rec,
                conflict_columns=["name"],
                update_columns=["roomid", "target", "targetedby", "is_alive", "state"],
                mogrify=False,
                conn=conn,
                commit=False,
            ):
                io.echo("mm.bot.save.110: upsert failed", level="error")
                return False

            with database.cursor(conn) as cur:
                q = database.query(
                    "DELETE FROM $murdermotel.npc_player_items WHERE npcmoniker = :npcmoniker",
                    npcmoniker=self.name,
                )
                cur.execute(q, {"npcmoniker": self.name})
                for i in self.items:
                    m = {"npcmoniker": self.name, "itemname": i.name}
                    if not database.insert(
                        self.args,
                        f"{libmm.SCHEMA}.npc_player_items",
                        m,
                        returnid=False,
                        mogrify=False,
                        conn=conn,
                        commit=False,
                    ):
                        io.echo("mm.bot.save.120: insert failed", level="error")
                        return False
            return True

        conn = kwargs.get("conn", None) or self.conn
        if conn is None:
            if self.pool is None:
                io.echo(f"mm.bot.save.100: {self.pool=}", level="error")
                return False
            with database.connect(self.args, pool=self.pool) as conn:
                return _work(conn)
        else:
            return _work(conn)


def access(args: argparse.Namespace, op: str, **kwargs: Any) -> bool:
    return op in ("init", "run", "turn", "main")


def init(args: argparse.Namespace, obj=None, room=None, **kwargs: Any) -> bool:
    return True


def buildargs(args, obj=None, room=None, **kwargs):
    return None


@fatal_on_db_error
def main(args: argparse.Namespace, **kwargs: Any) -> bool:
    return True


def turn(args: argparse.Namespace, **kwargs: Any) -> bool:
    obj = kwargs.get("obj")
    if obj is None:
        io.echo("Bot does not exist!")
        return False
    return obj.on_turn(args, **kwargs)


def load(args: argparse.Namespace, moniker: str, **kwargs) -> Optional[Bot]:
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT * FROM $murdermotel.npc WHERE name = :moniker AND is_bot = true",
                moniker=moniker,
            )
            cur.execute(q, {"moniker": moniker})
            if cur.rowcount == 0:
                return None

            rec = cur.fetchone()
            b = build(args, rec, **kwargs)
            b.items = getitems(args, moniker, conn=conn)
            return b

    conn = kwargs.get("conn")
    if conn is None:
        pool = kwargs.get("pool")
        if pool is None:
            io.echo("mm.bot.load.100: no pool", level="error")
            return None
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def create(
    args: argparse.Namespace, moniker: str, mode: Optional[str] = None, **kwargs
) -> Optional[Bot]:
    def _work(conn):
        nonlocal mode
        if mode is None:
            player_count = get_player_count(args, conn=conn)
            mode = select_mode_by_distribution(player_count)

        b = Bot(args, name=moniker, mode=mode, **kwargs)
        rec = b.buildrec()

        if not database.upsert(
            args,
            f"{libmm.SCHEMA}.npc",
            rec,
            conflict_columns=["name"],
            update_columns=["roomid", "target", "targetedby", "is_alive", "state"],
            mogrify=False,
            conn=conn,
            commit=False,
        ):
            io.echo("mm.bot.create.110: upsert failed", level="error")
            return None

        loaded = load(args, moniker, conn=conn)
        return loaded

    conn = kwargs.get("conn")
    if conn is None:
        pool = kwargs.get("pool")
        if pool is None:
            io.echo("mm.bot.create.100: no pool", level="error")
            return None
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def save(args: argparse.Namespace, bot: Bot, **kwargs) -> bool:
    return bot.save(**kwargs)


def getitems(args: argparse.Namespace, moniker: str, **kwargs):
    def _work(conn):
        items = []
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT * FROM $murdermotel.npc_player_items WHERE npcmoniker = :moniker",
                moniker=moniker,
            )
            cur.execute(q, {"moniker": moniker})
            if cur.rowcount == 0:
                return items
            for rec in cur.fetchall():
                item = libitem.load(args, rec["itemname"], conn=conn)
                if item is None:
                    io.echo(f"mm.bot.getitems: {item=}", level="error")
                    break
                items.append(item)
            return items

    conn = kwargs.get("conn")
    if conn is None:
        pool = kwargs.get("pool")
        if pool is None:
            io.echo("mm.bot.getitems.100: no pool", level="error")
            return []
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def exists(args: argparse.Namespace, moniker: str, **kwargs) -> bool:
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT name FROM $murdermotel.npc WHERE name = :moniker AND is_bot = true",
                moniker=moniker,
            )
            cur.execute(q, {"moniker": moniker})
            return cur.rowcount > 0

    conn = kwargs.get("conn")
    if conn is None:
        pool = kwargs.get("pool")
        if pool is None:
            io.echo("mm.bot.exists.100: no pool", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def build(args: argparse.Namespace, rec: dict, **kwargs) -> Bot:
    conn = kwargs.get("conn")

    state = kwargs.get("state")

    b = Bot(
        args,
        name=rec.get("name"),
        roomid=rec.get("roomid"),
        target=rec.get("target"),
        targetedby=rec.get("targetedby"),
        is_alive=rec.get("is_alive", True),
        mode=state.get("mode", libmm.BOT_MODE_HYBRID)
        if state
        else libmm.BOT_MODE_HYBRID,
        conn=conn,
    )
    return b


def get_player_count(args, **kwargs) -> int:
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT COUNT(*) AS count FROM $murdermotel.player WHERE died IS NULL"
            )
            cur.execute(q)
            if cur.rowcount == 0:
                return 0
            return cur.fetchone()["count"]

    conn = kwargs.get("conn")
    if conn is None:
        pool = kwargs.get("pool")
        if pool is None:
            return 0
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def get_alive_bots(args, **kwargs) -> list:
    def _work(conn):
        bots = []
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT name FROM $murdermotel.npc WHERE is_bot = true AND is_alive = true"
            )
            cur.execute(q)
            for rec in cur.fetchall():
                b = load(args, rec["name"], conn=conn)
                if b:
                    bots.append(b)
            return bots

    conn = kwargs.get("conn")
    if conn is None:
        pool = kwargs.get("pool")
        if pool is None:
            io.echo("mm.bot.get_alive_bots.100: no pool", level="error")
            return []
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def get_all_huntable_entities(args, **kwargs) -> list:
    """Return list of all living players + bots."""

    def _work(conn):
        entities = []
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT moniker FROM $murdermotel.player WHERE died IS NULL"
            )
            cur.execute(q)
            for rec in cur.fetchall():
                entities.append({"name": rec["moniker"], "type": "player"})

        bots = get_alive_bots(args, conn=conn)
        for b in bots:
            entities.append({"name": b.name, "type": "bot", "obj": b})

        return entities

    conn = kwargs.get("conn")
    if conn is None:
        pool = kwargs.get("pool")
        if pool is None:
            io.echo("mm.bot.get_all_huntable_entities.100: no pool", level="error")
            return []
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def generate_bots(args, count: Optional[int] = None, **kwargs) -> list:
    """Generate bots with dynamic mode distribution."""

    def _work(conn):
        nonlocal count
        if count is None:
            player_count = get_player_count(args, conn=conn)
            count = min(player_count * libmm.BOT_COUNT_RATIO, libmm.BOT_MAX_COUNT)

        if count <= 0:
            return []

        existing = get_alive_bots(args, conn=conn)
        if len(existing) >= libmm.BOT_MAX_COUNT:
            return existing

        needed = min(count, libmm.BOT_MAX_COUNT - len(existing))
        bots = []

        for _ in range(needed):
            name = get_bot_name_unique(args, conn=conn)
            player_count = get_player_count(args, conn=conn)
            mode = select_mode_by_distribution(player_count)
            b = create(args, name, mode, conn=conn)
            if b:
                bots.append(b)

        return bots

    conn = kwargs.get("conn")
    if conn is None:
        pool = kwargs.get("pool")
        if pool is None:
            io.echo("mm.bot.generate_bots.100: no pool", level="error")
            return []
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def assign_targets(args, player_monikers: list, bots: list, **kwargs) -> None:
    """Assign bidirectional targets between players and bots."""

    def _work(conn):
        if not player_monikers or not bots:
            return

        all_entities = []

        for moniker in player_monikers:
            with database.cursor(conn) as cur:
                q = database.query(
                    "SELECT bodycount, points, turn FROM $murdermotel.player WHERE moniker = :moniker",
                    moniker=moniker,
                )
                cur.execute(q, {"moniker": moniker})
                if cur.rowcount > 0:
                    rec = cur.fetchone()
                    all_entities.append(
                        {
                            "name": moniker,
                            "type": "player",
                            "bodycount": rec.get("bodycount", 0) or 0,
                            "points": rec.get("points", 0) or 0,
                            "turn": rec.get("turn", 0) or 0,
                        }
                    )

        for bot in bots:
            all_entities.append(
                {
                    "name": bot.name,
                    "type": "bot",
                    "bodycount": 0,
                    "points": 0,
                    "turn": 0,
                }
            )

        for player_moniker in player_monikers:
            target = weighted_select(
                [e for e in all_entities if e["name"] != player_moniker]
            )
            if target:
                with database.cursor(conn) as cur:
                    sql = f"update {libmm.SCHEMA}.player set target=%s where moniker=%s"
                    cur.execute(sql, (target["name"], player_moniker))
                    sql = f"update {libmm.SCHEMA}.npc set targetedby=%s where name=%s and is_bot=true"
                    cur.execute(sql, (player_moniker, target["name"]))

        for bot in bots:
            target = weighted_select([e for e in all_entities if e["name"] != bot.name])
            if target:
                bot.target = target["name"]
                bot.save(conn=conn)

    conn = kwargs.get("conn")
    if conn is None:
        pool = kwargs.get("pool")
        if pool is None:
            io.echo("mm.bot.assign_targets.100: no pool", level="error")
            return
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def ensure_valid_target(args, bot: Bot, **kwargs) -> bool:
    """Ensure bot has a valid target. Reassign if needed."""

    def _work(conn):
        if bot.target is None:
            return True

        with database.cursor(conn) as cur:
            params = {"target": bot.target}
            q = database.query(
                "SELECT is_alive FROM $murdermotel.npc WHERE name = :target AND is_bot = true",
                **params,
            )
            cur.execute(q, params)
            if cur.rowcount == 0 or not cur.fetchone()["is_alive"]:
                alive_bots = get_alive_bots(args, conn=conn)
                other_entities = [
                    {
                        "name": b.name,
                        "type": "bot",
                        "bodycount": 0,
                        "points": 0,
                        "turn": 0,
                    }
                    for b in alive_bots
                    if b.name != bot.name
                ]

                with database.cursor(conn) as cur2:
                    params = {"botname": bot.name}
                    q = database.query(
                        "SELECT moniker, bodycount, points, turn FROM $murdermotel.player WHERE died IS NULL AND moniker != :botname",
                        **params,
                    )
                    cur2.execute(q, params)
                    for rec in cur2.fetchall():
                        other_entities.append(
                            {
                                "name": rec["moniker"],
                                "type": "player",
                                "bodycount": rec.get("bodycount", 0) or 0,
                                "points": rec.get("points", 0) or 0,
                                "turn": rec.get("turn", 0) or 0,
                            }
                        )

                if other_entities:
                    new_target = weighted_select(other_entities)
                    bot.target = new_target["name"]
                    bot.save(conn=conn)
                return True
        return True

    conn = kwargs.get("conn")
    if conn is None:
        pool = kwargs.get("pool")
        if pool is None:
            io.echo("mm.bot.ensure_valid_target.100: no pool", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)
