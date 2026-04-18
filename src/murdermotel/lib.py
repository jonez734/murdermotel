from __future__ import annotations

import argparse
import copy
from typing import Optional

from bbsengine6 import io, database, util, member, screen, module
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
Item = libitem.Item

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

# Bot modes
BOT_MODE_STATIC = "static"
BOT_MODE_SIMPLE = "simple"
BOT_MODE_FULL = "full"
BOT_MODE_HYBRID = "hybrid"


def _stub_turn(args: argparse.Namespace, /, **kwargs: dict) -> bool | None:
    pass


def _stub_escape(args: argparse.Namespace, /, **kwargs: dict) -> int | None:
    pass


OP_TO_STUB = {
    "turn": _stub_turn,
    "escape": _stub_escape,
}


def get_op(module_ref: str, op: str, args) -> callable | None:
    """Get an optional operation function from murdermotel's op map."""
    m = module.get(module_ref, args)
    stub = OP_TO_STUB.get(op)
    if stub is None:
        return None
    if module.check_func(m, op, stub, silent=True):
        return getattr(m, op)
    return None


class Player(Living):
    modulepath: Optional[str] = "player"

    def __init__(self, args, **kwargs):
        super().__init__(args)
        self.fields = (
            "moniker",
            "roomid",
            "turn",
            "moves",
            "membermoniker",
            "datelastplayed",
            "points",
            "bodycount",
        )
        self.args = args
        self.moniker = member.getcurrentmoniker(args, **kwargs)  # getmembername(args)
        self.turn = 1
        self.moves = DEFAULTMOVESPERTURN
        self.datelastplayed = "now()"
        self.membermoniker = member.getcurrentmoniker(
            args, **kwargs
        )  # getcurrentmemberid(args)
        self.items = []
        self.isdirty = False
        self.points = 0
        self.bodycount = 0
        self.conn = kwargs.get("conn", None)
        self.pool = kwargs.get("pool", None)
        registry.register(self)

    def __repr__(self):
        buf = ""
        for f in self.fields:
            buf += "%s=%r " % (f, getattr(self, f))
        return buf

    def __str__(self):
        status = "alive" if self.moves > 0 else "dead"
        buf = f"{self.moniker} ({status} {self.moves} {self.turn} {self.healthpoints})"
        return buf

    def short(self):
        return f":person: {self.moniker}"

    def weapons(self, items=None):
        if items is None:
            items = copy.deepcopy(self.items)

        def find(shortname):
            for x in range(0, len(items)):
                if items[x].name == shortname:
                    return x
            return None

        components = [
            ["axe", "axeblade", "axehandle"],
            ["pistol", "pistol", "bullets"],
            ["chlorine", "chlorinegas", "gassprayer"],
            ["fire", "lighterfluid", "flamethrower"],
            ["acid", "industrialacid", "acidsprayer"],
        ]

        w = []
        for fortytwo in components:
            name = fortytwo[0]
            c1 = fortytwo[1]
            c2 = fortytwo[2]

            if find(c1) is not None and find(c2) is not None:
                i1 = find(c1)
                if i1 is not None:
                    del items[i1]

                i2 = find(c2)
                if i2 is not None:
                    del items[i2]

                io.echo(
                    f"complete weapon {name!r} found. i1={i1!r} i2={i2!r}",
                    level="debug",
                )
                w.append(name + " (weapon)")
        return w

    def finditem(self, shortname):
        if self.args.debug is True:
            io.echo(
                f"Room.finditem.100: {self.items=} {self.shortname=}", level="debug"
            )
        for x in range(0, len(self.items)):
            if self.args.debug is True:
                io.echo(f"room.finditem.120: name={self.items[x].name}", level="debug")
            if (
                self.items[x].name.lower() == shortname.lower()
                or self.items[x].title.lower() == shortname.lower()
            ):
                return x
        return None

    def load(self, moniker) -> bool:
        def _work(conn):
            sql = "select * from murdermotel.player where moniker=%s"
            dat = (moniker,)
            with database.cursor(conn) as cur:
                cur.execute(sql, dat)
                if cur.rowcount == 0:
                    if self.args.debug is True:
                        io.echo(f"unable to load player {moniker!r}", level="debug")
                        return False

                rec = cur.fetchone()
                for f in self.fields:
                    setattr(self, f, rec[f])

                self.items = self.getitems() if hasattr(self, "getitems") else []

            return True

    def save(self, mogrify=False):
        p = {}
        for f in self.fields:
            p[f] = getattr(self, f)

        if libplayer.exists(self.args, self.moniker) is True:
            database.update(
                self.args,
                "murdermotel.player",
                self.moniker,
                p,
                primarykey="moniker",
                mogrify=mogrify,
                pool=self.pool,
            )
        else:
            if self.args.debug is True:
                io.echo(f"{self.classname}.save.140: insert", level="debug")
            if not database.insert(
                self.args,
                "murdermotel.player",
                p,
                primarykey="moniker",
                returnid=False,
                mogrify=mogrify,
                pool=self.pool,
            ):
                io.echo("mm.player.save.150: insert failed", level="error")
                return False

        with database.connect(self.args, pool=self.pool) as conn:
            with database.cursor(conn) as cur:
                sql = "delete from murdermotel.map_item_player where playermoniker=%s"
                dat = (self.moniker,)
                cur.execute(sql, dat)
                for i in self.items:
                    m = {}
                    m["itemname"] = i.name
                    m["playermoniker"] = self.moniker
                    if not database.insert(
                        self.args,
                        "murdermotel.map_item_player",
                        m,
                        returnid=False,
                        mogrify=True,
                        conn=conn,
                    ):
                        io.echo("mm.player.save.160: insert failed", level="error")
                        return False

            conn.commit()
        return True

    def info(self):
        io.echo(f"{{var:labelcolor}}Moves: {{var:valuecolor}}{self.moves}")
        io.echo(f"{{var:labelcolor}}Turns: {{var:valuecolor}}{self.turn}")
        io.echo(f"{{var:labelcolor}}Name:  {{var:valuecolor}}{self.moniker}")
        date = util.datestamp(self.datelastplayed)
        io.echo(f"{{var:labelcolor}}Date:  {{var:valuecolor}}{date}")
        items = copy.deepcopy(self.items)
        items = self.weapons(items) + items
        util.oxfordcomma(items)
        io.echo(f"{{var:labelcolor}}Items: {{var:valuecolor}}{items}")

    def getitems(self):
        items = copy.deepcopy(self.items)

        def findcomponent(shortname):
            # ttyio.echo(f"getitems.findcomponent.100: items={self.items!r} shortname={shortname}", level="debug")
            for x in range(0, len(items)):
                # ttyio.echo(f"getitems.findcomponent.120: name={items[x].name}", level="debug")
                if items[x].name == shortname:
                    return x
            return None

        return self.weapons(items) + items
        w = []

        components = [
            ["axe", "axeblade", "axehandle"],
            ["pistol", "pistol", "bullets"],
            ["chlorine", "chlorine", "gassprayer"],
            ["fire", "lighterfluid", "flamethrower"],
            ["acid", "industrialacid", "acidsprayer"],
        ]
        for fortytwo in components:
            # ttyio.echo(f"getitems.100: fortytwo={fortytwo!r}", level="debug")
            name = fortytwo[0]

            c1 = fortytwo[1]
            c2 = fortytwo[2]

            if findcomponent(c1) is not None and findcomponent(c2) is not None:
                i1 = findcomponent(c1)
                if i1 is not None:
                    del items[i1]

                i2 = findcomponent(c2)
                if i2 is not None:
                    del items[i2]

                io.echo(
                    f"complete weapon {name!r} found. i1={i1!r} i2={i2!r}",
                    level="debug",
                )
                w.append(name + " (weapon)")

        #      if self.finditem("pistol") and self.finditem("bullets"):
        #          w.append("pistol")
        #          del items["pistol"]
        #          del items["bullets"]
        #      if self.finditem("chlorine") and self.finditem("gassprayer"):
        #          w.append("chlorine")
        #          del items["chlorine"]
        #          del items["gassprayer"]
        #      if self.finditem("lighterfluid") and self.finditem("flamethrower"):
        #          w.append("fire")
        #          del items["lighterfluid"]
        #          del items["flamethrower"]
        #      if self.finditem("industrialacid") and self.finditem("acidsprayer"):
        #          w.append("acid")
        #          del items["industrialacid"]
        #          del items["acidsprayer"]
        io.echo(f"weapons={w!r}", level="debug")
        return w + items


class completeItemName(object):
    def __init__(self, args, **kwargs):
        self.roomid = kwargs["roomid"] if "roomid" in kwargs else None
        self.playermoniker = (
            kwargs["playermoniker"] if "playermoniker" in kwargs else None
        )
        self.pool = kwargs.get("pool", None)
        self.args = args

        if self.args.debug is True:
            io.echo(f"completeItemName.100: kwargs={kwargs}", level="debug")

    def complete(self: object, text: str, state: int):
        if self.args.debug is True:
            io.echo("completeItemName.140: complete called", level="debug")

        if self.args.debug is True:
            io.echo(
                f"completeItemName.160: building vocab. self.roomid={self.roomid!r}, self.playermoniker={self.playermoniker!r}",
                level="debug",
            )

        if self.roomid is not None:
            sql = "select name from murdermotel.item as i, murdermotel.map_item_room as m where i.name = m.itemname and m.roomid=%s"
            dat = (self.roomid,)
        elif self.playermoniker is not None:
            sql = "select name from murdermotel.item as i, murdermotel.map_item_player as m where i.name = m.itemname and m.playermoniker=%s"
            dat = (self.playermoniker,)
        else:
            sql = "select name from murdermotel.item as i"
            dat = ()

        if self.pool is None:
            io.echo("completeItemName.120: pool is None", level="error")
            return [None]

        with database.connect(self.args, pool=self.pool) as conn:
            with database.cursor(conn) as cur:
                if self.args.debug is True:
                    io.echo(f"completeItemName.120: mogrify={cur.mogrify(sql, dat)!r}")
                cur.execute(sql, dat)

                vocab = []
                for rec in util.resultiter(cur):
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
    return module.runmodule(args, x, **kwargs)


# @since 20260410
def runmodule(args, op: str, modulename: str, **kwargs: dict):
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

    kwargs["operation"] = op

    if op in ("turn", "escape"):
        func = get_op(fullname, op, args)
        if func is None:
            if debug:
                io.echo(f"{fullname} has no {op}()", level="debug")
            return True
        return module.runcallback(args, func, **kwargs)

    if not module.check(args, fullname, **kwargs):
        return False

    return module.runmodule(args, fullname, **kwargs)


def buildargs(args=None, **kwargs):
    parser = argparse.ArgumentParser("murdermotel")

    parser.add_argument("--verbose", action="store_true", dest="verbose")
    parser.add_argument("--debug", action="store_true", dest="debug")
    parser.add_argument(
        "--terminalwidth",
        action="store",
        dest="terminalwidth",
        default=io.terminal.width(),
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
            sql = f"select count(*) from {SCHEMA}.item"
            cur.execute(sql)
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
            sql = f"select count(*) from {SCHEMA}.defense"
            cur.execute(sql)
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
            sql = f"select count(*) from {SCHEMA}.npc"
            cur.execute(sql)
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
            sql = "select * from murdermotel.item as i where name=%s"
            dat = (name,)
            cur.execute(sql, dat)
            if cur.rowcount == 0:
                return None
            rec = cur.fetchone()
            i = Item(args)
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
            sql = "select moniker from murdermotel.player as p where p.roomid=%s"
            dat = (roomid,)
            cur.execute(sql, dat)
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
            sql = f"select count(*) from {SCHEMA}.map_item_player"
            cur.execute(sql)
            if cur.rowcount > 0:
                res = cur.fetchone()
                count += res["count"]
            sql = f"select count(*) from {SCHEMA}.map_item_room"
            cur.execute(sql)
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
            sql = f"delete from {SCHEMA}.map_item_player"
            cur.execute(sql)
            sql = f"delete from {SCHEMA}.map_item_room"
            cur.execute(sql)
            return True

    def _work(conn):

        if clear is True:
            _clearitemmaps(conn)

        with database.cursor(conn) as cur:
            sql = f"select name, serial from {SCHEMA}.item where kind in ('component', 'defense')"
            cur.execute(sql)
            if cur.rowcount == 0:
                io.echo("items not populated")
                return False

            rows = cur.fetchall()
            io.echo(f"distributeitems: distributing {len(rows)} items", level="debug")

            roomcount = libroom.getcount(args, conn=conn)
            min_room = 11
            max_room = roomcount - 1
            eligible_rooms = list(range(min_room, max_room))

            room_counts = {}
            room_items = {}

            for row in rows:
                item_name = row["name"]
                item_serial = row["serial"]

                placed = False
                for attempt in range(10):
                    roomid = random.choice(eligible_rooms)
                    count = room_counts.get(roomid, 0)
                    if count >= 3:
                        continue

                    same_item_in_room = room_items.get(roomid, set())
                    if item_name in same_item_in_room:
                        continue

                    m = {"roomid": roomid, "itemname": item_name, "serial": item_serial}
                    if not database.insert(
                        args,
                        f"{SCHEMA}.map_item_room",
                        m,
                        conn=conn,
                        returnid=False,
                    ):
                        io.echo("mm.populate_items.110: insert failed", level="error")
                        return False
                    room_counts[roomid] = count + 1
                    if roomid not in room_items:
                        room_items[roomid] = set()
                    room_items[roomid].add(item_name)
                    placed = True
                    break

                if not placed:
                    roomid = random.choice(eligible_rooms)
                    m = {"roomid": roomid, "itemname": item_name, "serial": item_serial}
                    if not database.insert(
                        args,
                        f"{SCHEMA}.map_item_room",
                        m,
                        conn=conn,
                        returnid=False,
                    ):
                        io.echo("mm.populate_items.120: insert failed", level="error")
                        return False
                    room_counts[roomid] = room_counts.get(roomid, 0) + 1
                    if roomid not in room_items:
                        room_items[roomid] = set()
                    room_items[roomid].add(item_name)

        return True

    clear = kwargs.get("clear", False)
    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"libmm.distributeitems.100: {pool=}", level="error")
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
