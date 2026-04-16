import argparse
import copy
import random
from typing import Optional

from bbsengine6 import io, database, util, member, screen, module
from . import room as libroom, boobytrap as libboobytrap, player as libplayer

BoobyTrap = libboobytrap.BoobyTrap

# @since 20220813
SCHEMA = "murdermotel"
PACKAGENAME = "murdermotel"
DEFAULTMOVESPERTURN = 60
TURNSPERDAY = 2
PLAYGROUNDSIZE = 140
MAXITEMSPERPLAYER = 5


def _stub_turn(args: argparse.Namespace, /, **kwargs: dict) -> bool | None:
    pass


def _stub_escape(args: argparse.Namespace, /, **kwargs: dict) -> int | None:
    pass


class ObjectRegistry:
    """Registry for active game objects (NPCs, items) that need turn processing."""

    def __init__(self):
        self._objects: list = []

    def register(self, obj) -> None:
        if obj not in self._objects:
            self._objects.append(obj)

    def unregister(self, obj) -> None:
        if obj in self._objects:
            self._objects.remove(obj)

    def get_by_room(self, roomid: int) -> list:
        return [obj for obj in self._objects if obj.roomid == roomid]

    def all(self) -> list:
        return list(self._objects)

    def clear(self) -> None:
        self._objects.clear()


registry = ObjectRegistry()


class Obj(object):
    modulepath = None

    def __init__(self, args):
        self.args = args
        self.table = "murdermotel.player"
        self.fields = ()
        self.classname = self.__class__.__name__

    def on_turn(self, args, room=None, **kwargs):
        if self.modulepath:
            return runmodule(args, "turn", self.modulepath, obj=self, room=room, **kwargs)
        return True

    def short(self) -> str:
        return f"{self.classname}"

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


class Living(Obj):
    def __init__(self, args):
        super().__init__(args)
        self.roomid = None

    def short(self):
        return "NEEDINFO.living"


class Item(Obj):
    def __init__(self, args):
        super().__init__(args)
        self.roomid = None
        self.fields = ("type", "name", "title", "usemessages")
        self.type = None
        self.name = None
        self.title = None
        self.usemessages = []

    def short(self):
        return "NEEDINFO.item"

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


class RabidWolf(Living):
    def __init__(self, args, **kwargs):
        super().__init__(args)
        self.name = "wolf"
        self.healthpoints = 35
        self.conn = kwargs.get("conn", None)
        self.pool = kwargs.get("pool", None)
        if self.pool:
            loaded = kwargs.get("loaded_wolf", None)
            if loaded:
                self.roomid = loaded.roomid
                self.healthpoints = loaded.healthpoints
            else:
                self.roomid = random.randint(10, libroom.getcount(args, **kwargs) - 10)
        else:
            self.roomid = random.randint(10, libroom.getcount(args, **kwargs) - 10)
        self.modulepath = None
        registry.register(self)

    def short(self):
        return ":wolf: rabid wolf"

    def buildrec(self, **kwargs):
        rec = {}
        rec["name"] = self.name
        rec["roomid"] = self.roomid
        rec["healthpoints"] = self.healthpoints
        return rec

    def on_turn(self, args, room=None, **kwargs) -> bool:
        import random as randomlib

        player = kwargs.get("player", None)
        if player is None:
            io.echo("You do not exist! Go Away!")
            util.logentry(
                "murdermotel.rabidwolf.turn.100: player does not exist",
                logger_name="murdermotel",
            )
            return False

        attacked = kwargs.get("attacked", False)
        ignored = kwargs.get("ignored", False)

        WOLF_AUTO_ATTACK_CHANCE = 6

        if attacked:
            if util.diceroll(10, mode="single") < WOLF_AUTO_ATTACK_CHANCE:
                damage = randomlib.randint(1, 10) + 10
                io.echo(f"damage={damage}", level="debug")
                io.echo(
                    f"The {self.short()} claws you for {util.pluralize(damage, 'move', 'moves')}"
                )
                player.moves -= damage
                if player.moves < 0:
                    player.moves = 0
                    io.echo("You are out of moves. You are dead.")
                player.save()

        if ignored:
            if util.diceroll(10, mode="single") < WOLF_AUTO_ATTACK_CHANCE:
                io.echo(f"The {self.short()} attacks you!")
                damage = randomlib.randint(1, 10) + 10
                io.echo(f"damage={damage}", level="debug")
                io.echo(
                    f"The {self.short()} claws you for {util.pluralize(damage, 'move', 'moves')}"
                )
                player.moves -= damage
                if player.moves < 0:
                    player.moves = 0
                    io.echo("You are out of moves. You are dead.")
                player.save()

        pool = getattr(self, "pool", None)
        if pool:
            self.save()

            return True

    def save(self, **kwargs) -> bool:
        def _work(conn):
            rec = self.buildrec()
            database.update(
                self.args,
                f"{SCHEMA}.rabidwolf",
                self.name,
                rec,
                primarykey="name",
                conn=conn,
            )
            return True

        conn = kwargs.get("conn", None) or self.conn
        if conn is None:
            if self.pool is None:
                io.echo(f"mm.RabidWolf.save.100: {self.pool=}", level="error")
                return False
            with database.connect(self.args, pool=self.pool) as conn:
                _work(conn)
        else:
            _work(conn)
        return True


class Thief(Living):
    def __init__(self, args, **kwargs):
        super().__init__(args)
        self.name = "thief"
        self.bag = []
        self.healthpoints = 35
        self.conn = kwargs.get("conn", None)
        self.pool = kwargs.get("pool", None)
        if self.pool:
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
        self.modulepath = None
        registry.register(self)

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
        import random as randomlib

        player = kwargs.get("player", None)
        if player is None:
            io.echo("You do not exist! Go Away!")
            util.logentry(
                "murdermotel.thief.main.100: player does not exist", prg="murdermotel"
            )
            return False

        io.echo("THIEF! THIEF!  You were ATTACKED!")
        player.moves -= 5

        if util.diceroll(10) < 4:
            if not player.items:
                stolen = None
            else:
                idx = randomlib.randint(0, len(player.items) - 1)
                stolen = player.items.pop(idx)
                self.items.append(stolen)
            if stolen:
                io.echo(f"The thief stole {stolen.name} from you!")

        if self.pool:
            self.save()

        player.save()
        return True

    def save(self, **kwargs) -> bool:
        def _work(conn):
            rec = self.buildrec()
            database.update(
                self.args,
                f"{SCHEMA}.thief",
                self.name,
                rec,
                primarykey="name",
                conn=conn,
            )

            with database.cursor(conn) as cur:
                sql = f"delete from {SCHEMA}.map_item_thief where thiefname=%s"
                dat = (self.name,)
                cur.execute(sql, dat)

                for i in self.items:
                    m = {}
                    m["itemname"] = i.name
                    m["thiefname"] = self.name
                    database.insert(
                        self.args,
                        f"{SCHEMA}.map_item_thief",
                        m,
                        returnid=False,
                        mogrify=True,
                        conn=conn,
                    )
            return True

        conn = kwargs.get("conn", None) or self.conn
        if conn is None:
            if self.pool is None:
                io.echo(f"mm.Thief.save.100: {self.pool=}", level="error")
                return False
            with database.connect(self.args, pool=self.pool) as conn:
                _work(conn)
        else:
            _work(conn)
        return True


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
def runmodule(args, operation: str, modulename: str, **kwargs: dict):
    """
    Run an external module by name, delegating to bbsengine6.module.

    Passes all context via kwargs:
        obj = kwargs.get("obj")      # Living or Item object
        room = kwargs.get("room")    # Room object
        player = kwargs.get("player")  # Player object

    Args:
        args: argparse.Namespace
        operation: str - "run", "turn", "escape", etc.
        modulename: str - module name (e.g., "player", "thief", "lobby")
        **kwargs: additional arguments including obj, room, player

    Returns:
        bool - True if successful, False on error
    """
    fullname = f"{PACKAGENAME}.{modulename}"

    debug = getattr(args, "debug", False) if args else False
    if debug:
        io.echo(f"lib.runmodule.100: {operation=} {fullname=}", level="debug")

    kwargs["operation"] = operation

    if operation in ("turn", "escape"):
        m = module.get(fullname, args)
        stub = _stub_turn if operation == "turn" else _stub_escape
        if not module.check_func(m, operation, stub, silent=True):
            if debug:
                io.echo(f"{fullname} has no {operation}()", level="debug")
            return True
        func = getattr(m, operation)
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
    database.buildargdatabasegroup(parser, defaults, suppress=True)
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
