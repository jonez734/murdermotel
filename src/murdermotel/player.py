import argparse
import copy
import datetime

from bbsengine6 import member, database, io, util

from . import item as libitem, lib as libmm

FIELDS = (
    "moniker",
    "roomid",
    "turn",
    "moves",
    "bodycount",
    "points",
    "died",
    "modulepath",
    "membermoniker",
    "datelastplayed",
    "datecreated",
    "target",
    "targetedby",
)


def access(args, op, **kwargs) -> bool:
    return op in ("init", "run", "turn")


def init(args, obj=None, room=None, **kwargs) -> bool:
    return True


def buildargs(args, obj=None, room=None, **kwargs):
    return None


def main(args, **kwargs) -> bool:
    return True


def turn(args, **kwargs) -> bool:
    obj = kwargs.get("obj")
    if obj is None:
        return False
    return True


class Player(object):
    args: argparse.Namespace
    roomid: int | None
    died: int | None
    modulepath: str | None
    moniker: str
    turn: int
    moves: int
    datelastplayed: datetime.datetime
    items: list
    isdirty: bool
    points: int
    bodycount: int
    membermoniker: str | None
    pool: object
    conn: object
    exits: dict
    datecreated: datetime.datetime | None
    target: str | None
    targetedby: str | None

    def __init__(self, args, **kwargs):
        self.args = args
        self.roomid = None
        self.died = None
        self.modulepath = None
        self.moniker = member.getcurrentmoniker(args) or ""
        self.turn = 1
        self.moves = libmm.DEFAULTMOVESPERTURN
        self.datelastplayed = datetime.datetime.now(datetime.timezone.utc)
        self.items = []
        self.isdirty = False
        self.points = 0
        self.bodycount = 0
        self.membermoniker = None
        self.pool = kwargs.get("pool", None)
        self.conn = kwargs.get("conn", None)
        self.exits = {}
        self.datecreated = datetime.datetime.now(datetime.timezone.utc)
        self.target = None
        self.targetedby = None

    def __repr__(self):
        buf = ""
        for f in FIELDS:
            buf += "%s=%r " % (f, getattr(self, f))
        return buf

    def on_turn(self, args, room=None, **kwargs):
        if self.modulepath:
            return libmm.runmodule(
                args, "turn", self.modulepath, obj=self, room=room, **kwargs
            )
        return True

    def __str__(self):
        status = "alive" if self.moves > 0 else "dead"
        buf = f"{self.moniker} ({status} {self.moves} {self.turn})"
        return buf

    def short(self) -> str:
        return f":person: {self.moniker}"

    def buildrec(self, **kwargs):
        rec = {}
        for f in FIELDS:
            rec[f] = getattr(self, f, None)
        return rec

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
        io.echo(
            f"Room.finditem.100: items={self.items!r} shortname={shortname}",
            level="debug",
        )
        for x in range(0, len(self.items)):
            io.echo(f"room.finditem.120: name={self.items[x].name}", level="debug")
            if (
                self.items[x].name.lower() == shortname.lower()
                or self.items[x].title.lower() == shortname.lower()
            ):
                return x
        return None

    def save(self, **kwargs):
        def _work(conn):
            rec = self.buildrec()
            io.echo(f"mm.player.save.300: {rec=}", level="debug")
            database.update(
                self.args,
                f"{libmm.SCHEMA}.player",
                self.moniker,  # type: ignore[arg-type]
                rec,
                primarykey="moniker",
                conn=conn,
            )

            with database.cursor(conn) as cur:
                q = database.query(
                    "DELETE FROM $murdermotel.map_item_player WHERE playermoniker = :playermoniker",
                    playermoniker=self.moniker,
                )
                cur.execute(q, {"playermoniker": self.moniker})
                io.echo(f"Player.save.220: {self.items=}", level="debug")
                for i in self.items:
                    io.echo(
                        f"Player.save.200: saving player item {i.name=}", level="debug"
                    )
                    m = {}
                    m["itemname"] = i.name
                    m["serial"] = i.serial
                    m["playermoniker"] = self.moniker
                    if not database.insert(
                        self.args,
                        f"{libmm.SCHEMA}.map_item_player",
                        m,
                        returnid=False,
                        mogrify=True,
                        conn=conn,
                    ):
                        io.echo("mm.player.save.130: insert failed", level="error")
                        return False
            return True

        conn = kwargs.get("conn", None)
        if conn is None:
            if self.pool is None:
                io.echo(f"mm.player.save.120: {self.pool=}", level="error")
                return False
            with database.connect(self.args, pool=self.pool) as conn:
                result = _work(conn)
                conn.commit()
                return result
        else:
            return _work(conn)

    def info(self):
        io.echo(f"{{var:labelcolor}}Moves: {{var:valuecolor}}{self.moves}")
        io.echo(f"{{var:labelcolor}}Turns: {{var:valuecolor}}{self.turn}")
        io.echo(f"{{var:labelcolor}}Name:  {{var:valuecolor}}{self.moniker}")
        if self.datelastplayed is not None:
            date = util.datestamp(self.datelastplayed)
            io.echo(f"{{var:labelcolor}}Date:  {{var:valuecolor}}{date}")
        items = copy.deepcopy(self.items)
        items = self.weapons(items) + items
        util.oxfordcomma(items)
        io.echo(f"{{var:labelcolor}}Items: {{var:valuecolor}}{items}")

    def getitems(self):
        items = copy.deepcopy(self.items)

        def findcomponent(shortname):
            for x in range(0, len(items)):
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

        return w + items


def load(args, moniker, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT * FROM $murdermotel.player WHERE moniker = :moniker",
                moniker=moniker,
            )
            cur.execute(q, {"moniker": moniker})
            if cur.rowcount == 0:
                io.echo(
                    f"mm.player.load.120: unable to load player. {moniker=}",
                    level="error",
                )
                return None

            rec = cur.fetchone()

            p = build(args, rec, **kwargs)
            if p is None:
                return None
            p.items = getitems(args, moniker, **kwargs)
            return p

    io.echo(f"mm.player.load.120: {kwargs=}", level="debug")
    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.player.load.100: {pool=}", level="error")
            return None
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def exists(args, moniker, **kwargs) -> bool:
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT moniker FROM $murdermotel.player WHERE moniker = :moniker",
                moniker=moniker,
            )
            cur.execute(q, {"moniker": moniker})
            if cur.rowcount == 0:
                return False
            return True

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.player.exists.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def count(args, membermoniker: str, **kwargs) -> int:
    def _work(conn) -> int:
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT COUNT(*) as count FROM $murdermotel.player WHERE membermoniker = :membermoniker",
                membermoniker=membermoniker,
            )
            cur.execute(q, {"membermoniker": membermoniker})
            if cur.rowcount == 0:
                io.echo("murdermotel.player.count.160: returning 0", level="debug")
                return 0
            rec = cur.fetchone()
            count = rec["count"] if rec["count"] > 0 else 0
            io.echo(f"murdermotel.player.count.120: {count=}", level="error")
            return count

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"murdermotel.player.count.160: {pool=}", level="error")
            return 0
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def getitems(args, playermoniker, **kwargs) -> list:
    def _work(conn) -> list:
        items: list = []
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT * FROM $murdermotel.map_item_player WHERE playermoniker = :playermoniker",
                playermoniker=playermoniker,
            )
            cur.execute(q, {"playermoniker": playermoniker})
            if cur.rowcount == 0:
                return items
            res = cur.fetchmany()
            for rec in res:
                serial = rec.get("serial")
                item = libitem.load(args, rec["itemname"], serial=serial)
                if item is None:
                    io.echo(f"mm.player.getitems: {item=}", level="error")
                    break
                items.append(item)
        return items

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"murdermotel.player.getitems.100: {pool=}", level="error")
            return []
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    else:
        return _work(conn)


class completePlayerName:
    args: argparse.Namespace
    matches: list
    debug: bool
    pool: object

    def __init__(self, args: argparse.Namespace, **kwargs):
        self.args = args
        self.matches = []
        self.debug = getattr(args, "debug", False)
        self.pool = kwargs.get("pool", None)

    def complete(self, text: str, state: int):
        if self.pool is None:
            io.echo(f"mm.player.completePlayerName.100: {self.pool=}", level="error")
            return [
                None,
            ]
        with database.connect(self.args, pool=self.pool) as conn:
            with database.cursor(conn) as cur:
                vocab = []
                q = database.query("SELECT moniker FROM $murdermotel.player")
                cur.execute(q)
                for rec in cur.fetchall():
                    vocab.append(rec["moniker"])
                results = [x for x in vocab if x.startswith(text)] + [None]
                return results[state]


def verifyPlayerNameFound(args, moniker: str, **kwargs: dict) -> bool:
    import argparse

    args = kwargs.get("args", argparse.Namespace())

    def _work(conn):
        q = database.query(
            "SELECT 1 FROM $murdermotel.player WHERE moniker = :moniker",
            moniker=moniker,
        )
        with database.cursor(conn) as cur:
            cur.execute(q, {"moniker": moniker})
            io.echo(
                f"verifyPlayerNameNotFound.100: mogrify={database.mogrifysql(cur, str(q), (moniker,))}",
                level="debug",
            )
            if cur.rowcount == 0:
                return False
            return True

    io.echo(f"verifyPlayerNameNotFound.120: {args=} {moniker=}", level="debug")
    pool = kwargs.get("pool", None)
    if pool is None:
        io.echo(f"empyre.player.verifyPlayerNameFound.160: {pool=}", level="error")
        return False

    with database.connect(args, pool=pool) as conn:
        return _work(conn)


def verifyPlayerNameNotFound(args, moniker: str, **kwargs: dict) -> bool:

    def _work(conn):
        q = database.query(
            "SELECT 1 FROM $murdermotel.player WHERE moniker = :moniker",
            moniker=moniker,
        )
        with database.cursor(conn) as cur:
            cur.execute(q, {"moniker": moniker})
            io.echo(
                f"verifyPlayerNameNotFound.100: mogrify={database.mogrifysql(cur, str(q), (moniker,))}",
                level="debug",
            )
            if cur.rowcount == 0:
                return True
            return False

    io.echo(f"verifyPlayerNameNotFound.120: {args=} {moniker=}", level="debug")
    pool = kwargs.get("pool", None)
    if pool is None:
        io.echo(f"empyre.player.verifyPlayerNameNotFound.160: {pool=}", level="error")
        return False

    with database.connect(args, pool=pool) as conn:
        return _work(conn)


def build(args, rec: dict, **kwargs) -> Player:
    p = Player(args, **kwargs)
    for f in FIELDS:
        setattr(p, f, rec.get(f))
    return p


def inputmoniker(
    prompt: str = "player moniker: ",
    oldvalue: str = "",
    args: argparse.Namespace | None = None,
    **kwargs: dict,
):
    if args is None:
        args_from_kw = kwargs.get("args")
        if isinstance(args_from_kw, argparse.Namespace):
            args = args_from_kw
        else:
            args = argparse.Namespace()
    elif not isinstance(args, argparse.Namespace):
        args = argparse.Namespace()
    verify = kwargs.pop("verify", verifyPlayerNameFound)
    moniker = io.inputstring(
        prompt,
        oldvalue,
        verify=verify,
        completer=completePlayerName(args, **kwargs),
        completerdelims="",
        **kwargs,
    )
    io.echo(f"libplayer.inputmoniker.160: {moniker=}", level="debug")
    return moniker


def create(args, playermoniker, **kwargs):
    pool = kwargs.get("pool", None)
    if pool is None:
        io.echo(f"mm.player.create.140: {pool=}", level="error")
        return False

    def _work(conn, playermoniker) -> "Player | None":
        p = Player(args, pool=pool)
        p.moniker = playermoniker
        p.membermoniker = member.getcurrentmoniker(args, **kwargs)
        p.datecreated = datetime.datetime.now(datetime.timezone.utc)

        rec = p.buildrec()
        rec["moniker"] = playermoniker
        rec["membermoniker"] = p.membermoniker
        rec["datecreated"] = datetime.datetime.now(datetime.timezone.utc)
        io.echo(f"mm.player.create.110: {rec=}", level="debug")

        if not database.upsert(
            args,
            f"{libmm.SCHEMA}.player",
            rec,
            conflict_columns=["moniker"],
            update_columns=[
                "roomid",
                "turn",
                "moves",
                "bodycount",
                "points",
                "died",
                "modulepath",
                "membermoniker",
                "datelastplayed",
                "datecreated",
            ],
            mogrify=True,
            conn=conn,
        ):
            io.echo("mm.player.create.115: upsert failed", level="error")
            return None

        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT * FROM $murdermotel.player WHERE moniker = :moniker",
                moniker=playermoniker,
            )
            cur.execute(q, {"moniker": playermoniker})
            if cur.rowcount > 0:
                p = load(args, playermoniker, **kwargs)
                return p

        io.echo("mm.player.create.120: player table corrupted", level="error")
        return None

    #    io.echo(f"player.new.100: {currentmembermoniker=}", level="debug")

    try:
        conn = kwargs.get("conn", None)
        if conn is None:
            pool = kwargs.get("pool", None)
            if pool is None:
                io.echo(f"empyre.lib.create.140: {pool=}", level="error")
                return False
            with database.connect(args, pool=pool) as conn:
                return _work(conn, playermoniker)
        else:
            return _work(conn, playermoniker)
    except Exception:
        io.echo_traceback("mm.player.create.100")
        raise
