import argparse
import json
import random
from typing import Any, Callable, Optional

from bbsengine6 import database, io, screen, util, module as bbsmodule
from bbsengine6.io import terminal
from . import room as libroom, boobytrap as libboobytrap, player as libplayer
from . import obj as libobj
from . import item as libitem
from . import rabidwolf as librabidwolf
from . import thief as libthief

BoobyTrap = libboobytrap.BoobyTrap
RabidWolf = librabidwolf.RabidWolf
Thief = libthief.Thief

ObjectRegistry = libobj.ObjectRegistry
registry = libobj.registry
Obj = libobj.Obj
Living = libobj.Living

# @since 20220813
SCHEMA = "murdermotel"
PACKAGENAME = "murdermotel"
DEFAULTMOVESPERTURN = 60
TURNSPERDAY = 2
PLAYGROUNDSIZE = 140
MAXITEMSPERPLAYER = 5

# Bot configuration
BOT_KILL_POINTS = 50
BOT_MAX_COUNT = 20
BOT_COUNT_RATIO = 1
BOT_STARTING_MOVES = 60
BOT_PICKUP_CHANCE = 0.3
BOT_DROP_CHANCE = 0.2
BOT_ATTACK_CHANCE = 0.4

# Weapon distribution mode:
#   'components' = original game: distribute components only, players assemble
#   'complete'   = distribute fully-built weapons directly into rooms
#   'both'       = distribute both components AND complete weapons
WEAPON_MODE = "components"

# Default number of complete weapon instances per recipe.
# Can be overridden per-recipe via weapon_recipe.count column.
DEFAULT_WEAPON_COUNT = 6

# Bot modes
BOT_MODE_STATIC = "static"
BOT_MODE_SIMPLE = "simple"
BOT_MODE_FULL = "full"
BOT_MODE_HYBRID = "hybrid"


def _stub_turn(args, **kwargs) -> bool:
    return True


def _stub_escape(args, **kwargs) -> int:
    return 0


def _stub_attempt(args, **kwargs) -> bool:
    return False


def _stub_success(args, **kwargs) -> int:
    return 0


OP_TO_STUB = {
    "turn": _stub_turn,
    "escape": _stub_escape,
    "attempt": _stub_attempt,
    "success": _stub_success,
    "solved": _stub_success,
    "win": _stub_success,
}


def get_op(module_ref: str, op: str, args) -> Optional[Callable]:
    """Get an optional operation function from murdermotel's op map."""
    io.echo(f"get_op: looking for {op} in {module_ref}")
    m = bbsmodule.get(module_ref, args)
    stub = OP_TO_STUB.get(op)
    if stub is None:
        io.echo(f"get_op: no stub for {op}")
        return None

    has_func = bbsmodule.check_func(m, op, stub, silent=False)
    io.echo(f"get_op: check_func({op})={has_func}")
    if has_func:
        return getattr(m, op)
    io.echo(f"get_op: returning None for {op}")
    return None


class completeItemName:
    args: argparse.Namespace
    roomid: int | None
    playermoniker: str | None
    pool: object

    def __init__(self, args: argparse.Namespace, **kwargs: Any):
        self.roomid = kwargs["roomid"] if "roomid" in kwargs else None
        self.playermoniker = (
            kwargs["playermoniker"] if "playermoniker" in kwargs else None
        )
        self.pool = kwargs.get("pool", None)
        self.args = args

        debug = getattr(self.args, "debug", False)
        if debug is True:
            io.echo(f"completeItemName.100: kwargs={kwargs}", level="debug")

    def complete(self, text: str, state: int):
        debug = getattr(self.args, "debug", False)
        if debug is True:
            io.echo("completeItemName.140: complete called", level="debug")

        if debug is True:
            io.echo(
                f"completeItemName.160: building vocab. self.roomid={self.roomid!r}, self.playermoniker={self.playermoniker!r}",
                level="debug",
            )

        if self.roomid is not None:
            q = database.query(
                "SELECT i.name FROM $murdermotel.item i JOIN $murdermotel.map_item_room m ON i.name = m.itemname WHERE m.roomid = :roomid",
                roomid=self.roomid,
            )
            dat = {"roomid": self.roomid}
        elif self.playermoniker is not None:
            q = database.query(
                "SELECT i.name FROM $murdermotel.item i JOIN $murdermotel.map_item_player m ON i.name = m.itemname WHERE m.playermoniker = :playermoniker",
                playermoniker=self.playermoniker,
            )
            dat = {"playermoniker": self.playermoniker}
        else:
            q = database.query("SELECT name FROM $murdermotel.item")
            dat = {}

        if self.pool is None:
            io.echo("completeItemName.120: pool is None", level="error")
            return [None]

        with database.connect(self.args, pool=self.pool) as conn:
            with database.cursor(conn) as cur:
                if debug is True:
                    io.echo(f"completeItemName.120: mogrify={cur.mogrify(q, dat)!r}")
                cur.execute(q, dat)

                vocab = []
                for rec in cur.fetchall():
                    vocab.append(rec["name"])

        results = [x for x in vocab if x.startswith(text)] + [None]
        return results[state]


def setarea(args, player, left, **kwargs):
    def right():
        help = " | F1: Help" if "help" in kwargs and kwargs["help"] is True else ""
        debug = " | debug" if args.debug is True else ""
        room = ""
        playername = ""
        moves = ""
        turn = ""

        buf = "murder motel"
        if player is not None:
            if player.isdirty is True:
                isdirty = "*"
            else:
                isdirty = ""

            turn = " | %s" % (util.pluralize(4 - player.turn, "turn", "turns"))

            if player.roomid is not None:
                room = f" | room #{player.roomid}"
                conn = kwargs.get("conn", None)
                pool = kwargs.get("pool", None)
                if conn is None and pool is None:
                    io.echo(f"libmm.setarea.100: {pool=}", level="error")
                    return False
                currentroom = libroom.load(args, player.roomid, **kwargs)
                if currentroom is False:
                    io.echo(f"{player.roomid=} does not exist!", level="error")
                    return False

                if currentroom and currentroom.shortname is not None:
                    room += " " + currentroom.shortname
            else:
                room = ""

            moves = " | %s" % (util.pluralize(player.moves, "move", "moves"))

            playername = f" | {isdirty}{player.moniker}"

        buf += f"{playername}{room}{turn}{moves}{debug}{help}"

        return buf

    screen.setbottombar(left, right)
    return


def init(args=None):
    #  ttyio.setvariable("optioncolor", "{white}{bggray}")
    #  ttyio.setvariable("menudesc", "{/bgcolor}{white}")
    #  ttyio.setvariable("valuecolor", "{/bgcolor}{green}")
    #  ttyio.setvariable("promptcolor", "{/bgcolor}{lightgray}")
    #  ttyio.setvariable("inputcolor", "{/bgcolor}{green}")
    return True


def access(args, op, **kwargs) -> bool:
    return op in ("init", "run", "turn", "buildargs")


# @since 20220813
def runsubmodule(args, submodule, **kwargs):
    #  io.echo("mudermotel.lib.runsubmodule.120: trace") # , level="debug", end="\n")
    x = f"{PACKAGENAME}.{submodule}"
    if args.debug is True:
        io.echo("lib.runsubmodule.100: x=%r" % (x), level="debug")
    return bbsmodule.runmodule(args, x, **kwargs)


# @since 20260410
def runmodule(args, op: str, modulename: str, **kwargs: Any):
    """
    Run an external module by name, delegating to bbsengine6.module.

    Passes all context via kwargs:
        obj = kwargs.get("obj")      # Living or Item object
        room = kwargs.get("room")    # Room object
        player = kwargs.get("player")  # Player object

    Args:
        args: argparse.Namespace
        op: str - "run", "turn", "escape", etc.
        modulename: str - module name (e.g., "player", "thief", "lobby")
        **kwargs: additional arguments including obj, room, player

    Returns:
        bool - True if successful, False on error
    """
    fullname = f"{PACKAGENAME}.{modulename}"

    debug = getattr(args, "debug", False) if args else False
    if debug:
        io.echo(f"lib.runmodule.100: {op=} {fullname=}", level="debug")

    kwargs["operation"] = op  # type: ignore[index]

    if op == "attempt":
        func = get_op(fullname, op, args)
        if func is None:
            io.echo(f"lib.runmodule: {fullname} has no {op}()")
            return False
        io.echo(f"lib.runmodule: calling {op}() from {fullname}")
        result = bbsmodule.runcallback(args, func, **kwargs)
        io.echo(f"lib.runmodule: {op}() returned {result}")
        return result

    if op == "success":
        func = get_op(fullname, op, args)
        if func is None:
            io.echo(f"lib.runmodule: {fullname} has no {op}()")
            return False
        io.echo(f"lib.runmodule: calling {op}() from {fullname}")
        result = bbsmodule.runcallback(args, func, **kwargs)
        io.echo(f"lib.runmodule: {op}() returned {result}")
        return result

    if op == "solved":
        func = get_op(fullname, op, args)
        if func is None:
            if debug:
                io.echo(f"{fullname} has no {op}()", level="debug")
            return False
        return bbsmodule.runcallback(args, func, **kwargs)

    if op == "win":
        func = get_op(fullname, op, args)
        if func is None:
            if debug:
                io.echo(f"{fullname} has no {op}()", level="debug")
            return False
        return bbsmodule.runcallback(args, func, **kwargs)

    if op == "turn":
        func = get_op(fullname, op, args)
        if func is None:
            if debug:
                io.echo(f"{fullname} has no {op}()", level="debug")
            return True
        return bbsmodule.runcallback(args, func, **kwargs)

    if not bbsmodule.check(args, fullname, **kwargs):
        return False

    return bbsmodule.runmodule(args, fullname, **kwargs)


def buildargs(args=None, **kwargs):
    parser = argparse.ArgumentParser("murdermotel")

    parser.add_argument("--verbose", action="store_true", dest="verbose")
    parser.add_argument("--debug", action="store_true", dest="debug")
    parser.add_argument(
        "--terminalwidth",
        action="store",
        dest="terminalwidth",
        default=terminal.width(),
    )
    # parser.add_argument("--node", action="store", dest="node", default="cyclops")

    defaults = {
        "databasename": "zoid6",
        "databasehost": "localhost",
        "databaseuser": None,
        "databaseport": 5432,
        "databasepassword": None,
    }
    database.buildargdatabasegroup(parser, defaults, suppress=False)
    return parser


def main(args, **kwargs) -> bool:
    return True


def getitemcount(args, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query("SELECT COUNT(*) AS count FROM $murdermotel.item")
            cur.execute(q)
            if cur.rowcount == 0:
                return 0
            row = cur.fetchone()
            return row["count"]

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"libmm.getitemcount.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def getdefensecount(args, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query("SELECT COUNT(*) AS count FROM $murdermotel.defense")
            cur.execute(q)
            if cur.rowcount == 0:
                return 0
            row = cur.fetchone()
            return row["count"]

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"libmm.getdefensecount.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def getnpccount(args, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query("SELECT COUNT(*) AS count FROM $murdermotel.npc")
            cur.execute(q)
            if cur.rowcount == 0:
                return 0
            row = cur.fetchone()
            return row["count"]

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo("libmm.getnpccount.100: {pool=}", level="error")
            return None
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def getitem(args, name, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            params = {"name": name}
            q = database.query(
                "SELECT * FROM $murdermotel.item WHERE name = :name", **params
            )
            cur.execute(q, params)
            if cur.rowcount == 0:
                return None
            rec = cur.fetchone()
            i = libitem.Item(args)
            for f in ("type", "name", "title", "usemessages"):
                setattr(i, f, rec.get(f, None))
            return i

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"libmm.getitem.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def getroomplayers(args, roomid, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT moniker FROM $murdermotel.player WHERE roomid = :roomid",
                roomid=roomid,
            )
            cur.execute(q)
            players = []
            if cur.rowcount > 0:
                for rec in database.resultiter(cur):
                    p = libplayer.load(args, rec["moniker"], conn=conn)
                    players.append(p)

            return players

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"libmm.getroomplayers.100: {pool=}", level="error")
            return []
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def countdistributeditems(args, **kwargs):
    def _work(conn):
        count = 0
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT COUNT(*) AS count FROM $murdermotel.map_item_player"
            )
            cur.execute(q)
            if cur.rowcount > 0:
                res = cur.fetchone()
                count += res["count"]
            q = database.query(
                "SELECT COUNT(*) AS count FROM $murdermotel.map_item_room"
            )
            cur.execute(q)
            if cur.rowcount > 0:
                res = cur.fetchone()
                count += res["count"]
        return count

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"libmm.countdistributed.100: {pool=}", level="error")
            return 0
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def distributeitems(args, **kwargs):
    import random

    def _clearitemmaps(conn):
        io.echo("libmm.distributeitems.100: _clearitemmaps called", level="debug")
        with database.cursor(conn) as cur:
            q = database.query("DELETE FROM $murdermotel.map_item_player")
            cur.execute(q)
            q = database.query("DELETE FROM $murdermotel.map_item_room")
            cur.execute(q)
            return True

    def _work(conn):
        if kwargs.get("clear", False):
            _clearitemmaps(conn)

        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT name, serial FROM $murdermotel.item WHERE kind IN ('component', 'defense')"
            )
            cur.execute(q)
            if cur.rowcount == 0:
                io.echo("items not populated")
                return False

            rows = cur.fetchall()
            io.echo(f"distributeitems: distributing {len(rows)} items", level="debug")

            roomcount = libroom.getcount(args, conn=conn)
            eligible_rooms = list(range(11, roomcount - 1))

        if not eligible_rooms:
            io.echo("distributeitems: no eligible rooms", level="error")
            return False

        random.shuffle(rows)

        room_state: dict[int, set[str]] = {r: set() for r in eligible_rooms}
        placements = []

        for row in rows:
            item_name = row["name"]
            item_serial = row["serial"]

            placed = False
            for roomid in eligible_rooms:
                if len(room_state[roomid]) >= 3:
                    continue
                if item_name in room_state[roomid]:
                    continue
                room_state[roomid].add(item_name)
                placements.append((roomid, item_name, item_serial))
                placed = True
                break

            if not placed:
                roomid = random.choice(eligible_rooms)
                room_state[roomid].add(item_name)
                placements.append((roomid, item_name, item_serial))

        if not placements:
            io.echo("distributeitems: no placements determined", level="error")
            return False

        q = database.query(
            "INSERT INTO $murdermotel.map_item_room (roomid, itemname, serial) VALUES ($1, $2, $3)"
        )

        with database.cursor(conn) as cur:
            cur.executemany(q.as_string(conn), placements)

        conn.commit()
        return True

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"libmm.distributeitems.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def countdistributedweapons(args, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT COUNT(*) AS count FROM $murdermotel.map_item_room AS m "
                "JOIN $murdermotel.item AS i ON i.name = m.itemname AND i.serial = m.serial "
                "WHERE i.kind = 'weapon'"
            )
            cur.execute(q)
            if cur.rowcount == 0:
                return 0
            return cur.fetchone()["count"]

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"libmm.countdistributedweapons.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def getweaponrecipecount(args, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT COUNT(*) AS count FROM $murdermotel.weapon_recipe"
            )
            cur.execute(q)
            row = cur.fetchone()
            return row["count"] if row else 0

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"libmm.getweaponrecipecount.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def distributeweapons(args, **kwargs):
    weaponmode = kwargs.pop("weaponmode", WEAPON_MODE)
    if weaponmode == "components":
        return True

    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query("SELECT * FROM $murdermotel.weapon_recipe ORDER BY name")
            cur.execute(q)
            recipes = cur.fetchall()
            if not recipes:
                io.echo(
                    "distributeweapons: no weapon_recipe entries found", level="info"
                )
                return True

        roomcount = libroom.getcount(args, conn=conn)
        eligible_rooms = list(range(11, roomcount - 1))
        if not eligible_rooms:
            io.echo("distributeweapons: no eligible rooms", level="error")
            return False

        total_weapons = sum(r["count"] or DEFAULT_WEAPON_COUNT for r in recipes)
        io.echo(
            f"distributeweapons: generating {total_weapons} complete weapons",
            level="debug",
        )

        weapon_items = []
        serial_by_name = {}

        for recipe in recipes:
            count = (
                recipe["count"] if recipe["count"] is not None else DEFAULT_WEAPON_COUNT
            )
            if count <= 0:
                continue
            name = recipe["name"]
            title = recipe["title"] or name
            messages = recipe["usemessages"] or []
            state = recipe["state"] or {}

            for _ in range(count):
                if name not in serial_by_name:
                    serial_by_name[name] = 0
                serial_by_name[name] += 1
                weapon_items.append(
                    {
                        "name": name,
                        "serial": serial_by_name[name],
                        "kind": "weapon",
                        "title": title,
                        "modulepath": None,
                        "usemessages": messages,
                        "state": state,
                    }
                )

        for item in weapon_items:
            messages = item["usemessages"] or []
            state_json = json.dumps(item["state"]) if item["state"] else "{}"
            messages_str = (
                "ARRAY[" + ", ".join(f"'{m}'" for m in messages) + "]"
                if messages
                else "NULL"
            )
            with database.cursor(conn) as cur:
                q_str = (
                    f"INSERT INTO murdermotel.item (name, serial, kind, title, modulepath, usemessages, state) "
                    f"VALUES ('{item['name']}', {item['serial']}, 'weapon', '{item['title']}', NULL, {messages_str}, '{state_json}') "
                    f"ON CONFLICT (name, serial) DO UPDATE SET kind = EXCLUDED.kind, title = EXCLUDED.title, usemessages = EXCLUDED.usemessages, state = EXCLUDED.state"
                )
                cur.execute(q_str)

        random.shuffle(weapon_items)
        room_state = {r: set() for r in eligible_rooms}
        placements = []

        for item in weapon_items:
            item_name = item["name"]
            item_serial = item["serial"]

            placed = False
            for roomid in eligible_rooms:
                if len(room_state[roomid]) >= 3:
                    continue
                if item_name in room_state[roomid]:
                    continue
                room_state[roomid].add(item_name)
                placements.append((roomid, item_name, item_serial))
                placed = True
                break

            if not placed:
                for roomid in eligible_rooms:
                    if len(room_state[roomid]) < 3:
                        room_state[roomid].add(item_name)
                        placements.append((roomid, item_name, item_serial))
                        placed = True
                        break

                if not placed:
                    roomid = random.choice(eligible_rooms)
                    room_state[roomid].add(item_name)
                    placements.append((roomid, item_name, item_serial))

        for roomid, item_name, item_serial in placements:
            with database.cursor(conn) as cur:
                cur.execute(
                    f"INSERT INTO murdermotel.map_item_room (roomid, itemname, serial) VALUES ({roomid}, '{item_name}', {item_serial}) ON CONFLICT (roomid, itemname, serial) DO NOTHING"
                )

        io.echo(
            f"distributeweapons: placed {len(placements)} weapons in rooms",
            level="debug",
        )
        conn.commit()
        return True

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"libmm.distributeweapons.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def reload_module(obj) -> bool:
    """Clear cached module on obj; will be re-imported on next runmodule() call."""
    obj.module = None
    io.echo(f"Reloaded module for {obj}", level="debug")
    return True


def reload_modulepath(modulepath: str) -> int:
    """Clear cached module on all registered objects with the given modulepath."""
    count = 0
    for obj in registry.all():
        if getattr(obj, "modulepath", None) == modulepath:
            reload_module(obj)
            count += 1
    io.echo(f"Reloaded {count} object(s) with modulepath={modulepath!r}", level="debug")
    return count


def reload_all_modules() -> int:
    """Clear cached module on all registered objects that have a modulepath."""
    count = 0
    for obj in registry.all():
        if getattr(obj, "modulepath", None) is not None:
            reload_module(obj)
            count += 1
    io.echo(f"Reloaded {count} object(s) total", level="debug")
    return count
