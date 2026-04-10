import argparse
import copy
import random
from typing import Optional

from bbsengine6 import io, database, util, member, screen, module
from . import player as libplayer, room as libroom

# @since 20220813
SCHEMA = "murdermotel"
PACKAGENAME = "murdermotel"
DEFAULTMOVESPERTURN = 60
TURNSPERDAY = 2
PLAYGROUNDSIZE = 140
MAXITEMSPERPLAYER = 5


class Obj(object):
    def __init__(self, args):
        self.args = args
        self.table = "murdermotel.player"
        self.fields = ()
        self.classname = self.__class__.__name__

    def load(self, name) -> bool:
        if self.args.debug is True:
            io.echo(f"{name}.load({self.classname})", level="debug")
        sql = f"select * from {self.table} where moniker=%s"
        dat = (name,)
        dbh = database.connect(self.args)
        cur = dbh.cursor()
        #    ttyio.echo("%s.load.100: %r" % (self.classname, cur.mogrify(sql, dat)), level="debug")
        cur.execute(sql, dat)
        if cur.rowcount == 0:
            io.echo(f"unable to load record {name!r}", level="error")
            return False

        rec = cur.fetchone()
        for f in self.fields:
            setattr(self, f, rec[f])

        return True

    def save(self):
        p = {}
        for f in self.fields:
            p[f] = getattr(self, f)

        io.echo(f"{self.classname}.save.100: p={p!r}", level="debug")

        dbh = database.connect(self.args)
        if self.args.debug is True:
            io.echo(f"{self.classname}.save.120: trying update", level="debug")
        res = database.update(
            self.args, self.table, self.name, p, primarykey="moniker", mogrify=True
        )
        if self.args.debug is True:
            io.echo(f"{self.classname}.save.140: res={res!r}", level="debug")
        if res == 0:
            if self.args.debug is True:
                io.echo(
                    f"{self.classname}.save.160: update failed, trying insert. p={p!r}",
                    level="debug",
                )
            database.insert(
                self.args,
                self.table,
                p,
                primarykey="name",
                returnid=False,
                mogrify=True,
            )
        self.isdirty = False
        dbh.commit()
        return True


class Living(object):
    module: Optional[str] = None

    def __init__(self, args):
        self.args = args
        self.roomid = None

    def on_turn(self, args, room=None, **kwargs) -> bool:
        """Called each turn when in same room as player."""
        if self.module:
            return runmodule(args, self, "turn", room=room, **kwargs)
        return True

    def short(self):
        return "NEEDINFO.living"


class Item(object):
    module: Optional[str] = None

    def __init__(self, args):
        super().__init__()
        self.roomid = None

    def on_turn(self, args, room=None, **kwargs) -> bool:
        """Called each turn when in same room as player."""
        if self.module:
            return runmodule(args, self, "turn", room=room, **kwargs)
        return True

    def short(self):
        return "NEEDINFO.item"


class RabidWolf(Living):
    def __init__(self, args, **kwargs):
        super().__init__(args)
        self.name = "wolf"
        self.healthpoints = 35
        pool = kwargs.get("pool", None)
        if pool:
            loaded = kwargs.get("loaded_wolf", None)
            if loaded:
                self.roomid = loaded.roomid
                self.healthpoints = loaded.healthpoints
            else:
                self.roomid = random.randint(10, libroom.getcount(args, **kwargs) - 10)
        else:
            self.roomid = random.randint(10, libroom.getcount(args, **kwargs) - 10)
        self.module = None

    def short(self):
        return ":wolf: rabid wolf"

    def buildrec(self, **kwargs):
        rec = {}
        rec["name"] = self.name
        rec["roomid"] = self.roomid
        rec["healthpoints"] = self.healthpoints
        return rec

    def on_turn(self, args, room=None, **kwargs) -> bool:
        from . import rabidwolf as libwolf

        return libwolf.turn(args, wolf=self, **kwargs)


class Thief(Living):
    def __init__(self, args, **kwargs):
        super().__init__(args)
        self.name = "thief"
        self.bag = []
        self.healthpoints = 35
        pool = kwargs.get("pool", None)
        if pool:
            loaded = kwargs.get("loaded_thief", None)
            if loaded:
                self.roomid = loaded.roomid
                self.healthpoints = loaded.healthpoints
                self.items = loaded.items
            else:
                self.roomid = random.randint(10, libroom.getcount(args, **kwargs) - 10)
        else:
            self.roomid = random.randint(10, libroom.getcount(args, **kwargs) - 10)
        self.items = []
        self.module = None

    def short(self):
        return ":supervillian: Thief"

    def buildrec(self, **kwargs):
        rec = {}
        rec["name"] = self.name
        rec["bag"] = self.bag
        rec["roomid"] = self.roomid
        rec["healthpoints"] = self.healthpoints
        return rec

    def on_turn(self, args, room=None, **kwargs) -> bool:
        from . import thief as libthief

        return libthief.turn(args, thief=self, **kwargs)


class BoobyTrap(Item):
    def __init__(self, args, **kwargs):
        super().__init__(args)
        self.name = "boobytrap"
        self.healthpoints = 20
        self.running = False
        self.timer = 0
        pool = kwargs.get("pool", None)
        if pool:
            loaded = kwargs.get("loaded_boobytrap", None)
            if loaded:
                self.roomid = loaded.roomid
                self.running = loaded.running
                self.timer = loaded.timer
            else:
                self.roomid = random.randint(
                    10, libroom.getcount(args, **kwargs) - 10 + 1
                )
        else:
            self.roomid = random.randint(10, libroom.getcount(args, **kwargs) - 10 + 1)
        self.playerid = None
        self.type = "boobytrap"
        self.module = "boobytrap"

    def short(self):
        return ":mousetrap: Booby-Trap"

    def buildrec(self, **kwargs):
        rec = {}
        rec["name"] = self.name
        rec["running"] = self.running
        rec["timer"] = self.timer
        return rec

    def on_turn(self, args, room=None, **kwargs) -> bool:
        from . import boobytrap as libboobytrap

        return libboobytrap.turn(args, boobytrap=self, **kwargs)


class Player(Living):
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
        self.pool = kwargs.get("pool", None)

    def __repr__(self):
        buf = ""
        for f in self.fields:
            buf += "%s=%r " % (f, getattr(self, f))
        return buf

    def __str__(self):
        status = "alive" if self.moves > 0 else "dead"
        buf = f"{self.moniker} ({status} {self.moves} {self.turn} {self.healthpoints})"
        return buf

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
            if self.items[x].name == shortname:
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
            database.insert(
                self.args,
                "murdermotel.player",
                p,
                primarykey="moniker",
                returnid=False,
                mogrify=mogrify,
                pool=self.pool,
            )

        with database.connect(self.args, pool=self.pool) as conn:
            with database.cursor(conn) as cur:
                sql = "delete from murdermotel.map_item_player where playermoniker=%s"
                dat = (self.moniker,)
                cur.execute(sql, dat)
                for i in self.items:
                    m = {}
                    m["itemname"] = i.name
                    m["playermoniker"] = self.moniker
                    database.insert(
                        self.args,
                        "murdermotel.map_item_player",
                        m,
                        returnid=False,
                        mogrify=True,
                        conn=conn,
                    )

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


currentplayer = None


def setcurrentplayer(player):
    global currentplayer
    currentplayer = player


def getcurrentplayer():
    global currentplayer
    return currentplayer


class completeItemName(object):
    def __init__(self, args, **kwargs):
        self.roomid = kwargs["roomid"] if "roomid" in kwargs else None
        self.playermoniker = (
            kwargs["playermoniker"] if "playermoniker" in kwargs else None
        )

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

        dbh = database.connect(self.args)
        cur = dbh.cursor()
        if self.args.debug is True:
            io.echo(f"completeItemName.120: mogrify={cur.mogrify(sql, dat)!r}")
        cur.execute(sql, dat)

        vocab = []
        for rec in util.resultiter(cur):
            vocab.append(rec["name"])

        results = [x for x in vocab if x.startswith(text)] + [None]
        return results[state]


class Item(object):
    def __init__(self, args):
        self.fields = ("type", "name", "title", "usemessages")
        self.args = args
        self.type = None
        self.name = None  # primary key
        self.title = None
        self.usemessages = []

    def __repr__(self):
        return f"{self.title} ({self.type})"

    def save(self):
        p = {}
        for f in self.fields:
            p[f] = getattr(self, f)

        if self.args.debug is True:
            io.echo(f"Item.save.100: p={p!r}", level="debug")

        if self.args.debug is True:
            io.echo("Item.save.140: trying update", level="debug")
        res = database.update(
            self.args, "murdermotel.item", self.name, p, primarykey="name", mogrify=True
        )
        io.echo(f"Item.save.120: res={res!r}", level="debug")
        if res == 0:
            if self.args.debug is True:
                io.echo(
                    f"Item.save.160: update failed, trying insert p={p!r}",
                    level="debug",
                )
            database.insert(
                self.args,
                "murdermotel.item",
                p,
                primarykey="name",
                returnid=False,
                mogrify=True,
            )
        database.commit(self.args)
        return True


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
                if currentroom is not None and currentroom.shortname is not None:
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


# @since 20220813
def runsubmodule(args, submodule, **kwargs):
    #  io.echo("mudermotel.lib.runsubmodule.120: trace") # , level="debug", end="\n")
    x = f"{PACKAGENAME}.{submodule}"
    if args.debug is True:
        io.echo("lib.runsubmodule.100: x=%r" % (x), level="debug")
    return module.runmodule(args, x, **kwargs)


# @since 20260410
def runmodule(args, obj, operation, room=None, **kwargs):
    """
    Run an external module operation on a Living or Item object.

    If obj.module is set, loads that module and calls the specified operation.
    If obj.module is None, returns True (no custom module).

    Extended ABI (in addition to standard bbsengine6 module ABI):
        init(args, obj, room, **kwargs) -> bool
        access(args, op, obj, room, **kwargs) -> bool
        buildargs(args, obj, room, **kwargs) -> argparse.ArgumentParser
        main(args, obj, room, **kwargs) -> bool
        turn(args, obj, room, **kwargs) -> bool  # called each turn

    Args:
        args: argparse.Namespace
        obj: Living or Item object with .module attribute
        operation: str - one of 'init', 'access', 'buildargs', 'main', 'turn'
        room: Optional[Room] - the current room
        **kwargs: additional arguments

    Returns:
        bool - True if successful, False on error
        For 'buildargs', returns argparse.ArgumentParser or None
    """
    if obj.module is None:
        return True

    debug = args.debug if hasattr(args, "debug") and args.debug else False

    if debug is True:
        io.echo(f"lib.runmodule.100: {obj.module=} {operation=}", level="debug")

    modulename = obj.module

    try:
        m = __import__(
            modulename, fromlist=["init", "access", "buildargs", "main", "turn"]
        )
    except ModuleNotFoundError:
        io.echo(f"module {modulename!r} not found", level="error")
        return False
    except Exception:
        io.echo_traceback(f"lib.runmodule: import {modulename}")
        return False

    if not hasattr(m, operation):
        if debug is True:
            io.echo(f"module {modulename} has no {operation}()", level="debug")
        return True

    func = getattr(m, operation)
    if not callable(func):
        io.echo(f"{modulename}.{operation} is not callable", level="error")
        return False

    try:
        if operation == "init":
            result = func(args, obj=obj, room=room, **kwargs)
        elif operation == "access":
            op = kwargs.get("op", "run")
            result = func(args, op, obj=obj, room=room, **kwargs)
        elif operation == "buildargs":
            result = func(args, obj=obj, room=room, **kwargs)
        elif operation == "main":
            result = func(args, obj=obj, room=room, **kwargs)
        elif operation == "turn":
            result = func(args, obj=obj, room=room, **kwargs)
        else:
            io.echo(f"unknown operation: {operation}", level="error")
            return False
    except Exception:
        io.echo_traceback(f"lib.runmodule: {modulename}.{operation}()")
        return False

    if debug is True:
        io.echo(
            f"lib.runmodule.200: {modulename}.{operation}() = {result}", level="debug"
        )

    return result if result is not None else True


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
    database.buildargdatabasegroup(parser, defaults, suppress=True)
    return parser


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
            sql = f"select name from {SCHEMA}.item"
            cur.execute(sql)
            if cur.rowcount == 0:
                io.echo("items not populated")
                return False

            rows = cur.fetchmany()
            item_rows = rows  # from your psycopg3 query
            item_names = [row["name"] for row in item_rows]
            io.echo(f"{item_names=}", level="debug")

            # Eligible room IDs: 10 to 140 inclusive
            roomcount = libroom.getcount(args, conn=conn)
            eligible_rooms = list(range(10, roomcount - 10))

            # Prepare result and room count tracking
            #      assignments = []
            room_counts = {}

            for item_name in item_names:
                while True:
                    roomid = random.choice(eligible_rooms)
                    count = room_counts.get(roomid, 0)
                    if count < 3:
                        map = {"roomid": roomid, "itemname": item_name}
                        database.insert(
                            args,
                            f"{SCHEMA}.map_item_room",
                            map,
                            conn=conn,
                            primarykey="itemname",
                        )
                        room_counts[roomid] = count + 1
                        break

        #      cur.executemany(f"insert into {SCHEMA}.map_item_room(roomid, itemname) values (%(roomid)s, %(itemname)s)", assignments)

        # Now `assignments` is ready for insertion
        # Example:
        # [{'roomid': 42, 'itemid': 'item1'}, {'roomid': 57, 'itemid': 'item2'}, ...]

        # Optionally, insert into the database
        # cur.executemany("INSERT INTO item_room_map (roomid, itemid) VALUES (%(roomid)s, %(itemid)s)", assignments)

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
