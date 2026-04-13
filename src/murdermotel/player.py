import argparse
import copy
import datetime
from typing import Any, Optional

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
    "module",
    "membermoniker",
    "datelastplayed",
    "datecreated",
)


def access(args, op, **kwargs) -> bool:
    return op in ("init", "run", "turn")


def init(args, obj=None, room=None, **kwargs) -> bool:
    return True


def buildargs(args, obj=None, room=None, **kwargs):
    return None


def main(args, **kwargs) -> bool:
    return True


def turn(args, obj=None, room=None, **kwargs) -> bool:
    if obj is None:
        return False
    return True


class Player(object):
    args: argparse.Namespace
    moniker: str
    turn: int
    moves: int
    datelastplayed: datetime.datetime
    items: list
    isdirty: bool
    points: int
    bodycount: int
    module: Optional[str]
    membermoniker: Optional[str]
    pool: Any
    roomid: Optional[int]
    exits: dict
    datecreated: Optional[datetime.datetime]

    def __init__(self, args, **kwargs):
        self.args = args
        self.moniker = member.getcurrentmoniker(args)
        self.turn = 1
        self.moves = libmm.DEFAULTMOVESPERTURN
        self.datelastplayed = datetime.datetime.now(datetime.timezone.utc)
        self.items = []
        self.isdirty = False
        self.points = 0
        self.bodycount = 0
        self.module = None
        self.membermoniker = None
        self.pool = kwargs.get("pool", None)
        self.roomid = None
        self.exits = {}
        self.datecreated = None

    def __repr__(self):
        buf = ""
        for f in FIELDS:
            buf += "%s=%r " % (f, getattr(self, f))
        return buf

    def __str__(self):
        status = "alive" if self.moves > 0 else "dead"
        buf = f"{self.moniker} ({status} {self.moves} {self.turn})"
        return buf

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
            if self.items[x].name == shortname:
                return x
        return None

    def save(self, **kwargs):
        def _work(conn):
            rec = self.buildrec()
            io.echo(f"mm.player.save.300: {rec=}", level="debug")
            database.update(
                self.args,
                f"{libmm.SCHEMA}.player",
                self.moniker,
                rec,
                primarykey="moniker",
                conn=conn,
            )

            with database.cursor(conn) as cur:
                sql = (
                    f"delete from {libmm.SCHEMA}.map_item_player where playermoniker=%s"
                )
                dat = (self.moniker,)
                cur.execute(sql, dat)
                io.echo(f"Player.save.220: {self.items=}", level="debug")
                for i in self.items:
                    io.echo(
                        f"Player.save.200: saving player item {i.name=}", level="debug"
                    )
                    m = {}
                    m["itemname"] = i.name
                    m["playermoniker"] = self.moniker
                    database.insert(
                        self.args,
                        f"{libmm.SCHEMA}.map_item_player",
                        m,
                        returnid=False,
                        mogrify=True,
                        conn=conn,
                    )
            return True

        conn = kwargs.get("conn", None)
        if conn is None:
            if self.pool is None:
                io.echo(f"mm.player.save.120: {self.pool=}", level="error")
                return False
            with database.connect(self.args, pool=self.pool) as conn:
                _work(conn)
        else:
            _work(conn)

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
            sql = f"select * from {libmm.SCHEMA}.player where moniker=%s"
            dat = (moniker,)
            cur.execute(sql, dat)
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

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.player.load.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def exists(args, moniker, **kwargs) -> bool:
    def _work(conn):
        with database.cursor(conn) as cur:
            sql = f"select moniker from {libmm.SCHEMA}.player where moniker=%s"
            dat = (moniker,)
            cur.execute(sql, dat)
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
    def _work(conn):
        sql: str = (
            "select count(moniker) from murdermotel.player where membermoniker=%s"
        )
        dat: tuple = (membermoniker,)
        with database.cursor(conn) as cur:
            cur.execute(sql, dat)
            if cur.rowcount == 0:
                io.echo("murdermotel.player.count.160: returning None", level="debug")
                return None
            rec = cur.fetchone()
            count = rec["count"] if rec["count"] > 0 else None
            io.echo(f"murdermotel.player.count.120: {count=}", level="error")
            return count

    conn = kwargs.get("conn", None)
    if conn is None:
        io.echo(f"murdermotel.player.count.140: {conn=}", level="error")
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"murdermotel.player.count.160: {pool=}")
            return None
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def getitems(args, playermoniker, **kwargs):
    def _work(conn):
        items = []
        with database.cursor(conn) as cur:
            sql = f"select * from {libmm.SCHEMA}.map_item_player where playermoniker=%s"
            dat = (playermoniker,)
            cur.execute(sql, dat)
            if cur.rowcount == 0:
                return items
            res = cur.fetchmany()
            for rec in res:
                item = libitem.load(args, rec["itemname"])
                if item is None:
                    io.echo(f"mm.player.getitems: {item=}", level="error")
                    break
                items.append(item)
            return items

    conn = kwargs.get("conn", None)
    if conn is None:
        io.echo(f"mm.player.getitems.140: {conn=}", level="error")
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"murdermotel.player.count.160: {pool=}")
            return None
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


class completePlayerName(object):
    def __init__(self, args, **kwargs):
        self.args = args
        self.matches = []
        self.debug = args.debug if "debug" in args else False
        self.pool = kwargs.get("pool", None)

    def complete(self: object, text: str, state: int):
        if self.pool is None:
            io.echo(f"mm.player.completePlayerName.100: {self.pool=}", level="error")
            return [
                None,
            ]
        with database.connect(self.args, pool=self.pool) as conn:
            with database.cursor(conn) as cur:
                vocab = []
                sql: str = f"select name from {libmm.SCHEMA}.player"
                dat: tuple = ()
                cur = conn.cursor()
                cur.execute(sql, dat)
                for rec in database.resultiter(cur):
                    vocab.append(rec["name"])
                results = [x for x in vocab if x.startswith(text)] + [None]
                return results[state]


def verifyPlayerNameFound(args, moniker: str, **kwargs: dict) -> bool:
    import argparse

    args = kwargs.get("args", argparse.Namespace())

    def _work(conn):
        sql: str = f"select 1 from {libmm.SCHEMA}.player where moniker=%s"
        dat: tuple = (moniker,)
        with database.cursor(conn) as cur:
            cur.execute(sql, dat)
            io.echo(
                f"verifyPlayerNameNotFound.100: mogrify={database.mogrifysql(cur, sql, dat)}",
                level="debug",
            )
            if cur.rowcount == 0:
                return False
            return True

    io.echo(f"verifyPlayerNameNotFound.120: {args=} {moniker=}", level="debug")
    pool = kwargs.get("pool", None)
    if pool is None:
        io.echo(f"empyre.player.verifyPlayerNameNotFound.160: {pool=}", level="error")
        return False

    with database.connect(args, pool=pool) as conn:
        return _work(conn)


def verifyPlayerNameNotFound(args, moniker: str, **kwargs: dict) -> bool:

    def _work(conn):
        sql: str = f"select 1 from {libmm.SCHEMA}.player where moniker=%s"
        dat: tuple = (moniker,)
        with database.cursor(conn) as cur:
            cur.execute(sql, dat)
            io.echo(
                f"verifyPlayerNameNotFound.100: mogrify={database.mogrifysql(cur, sql, dat)}",
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


def inputmoniker(prompt: str = "player moniker: ", oldvalue: str = "", **kwargs: dict):
    args = kwargs.pop("args", argparse.Namespace())
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

    def _work(conn, playermoniker) -> str:
        p = Player(args, pool=pool)
        p.moniker = playermoniker
        p.membermoniker = member.getcurrentmoniker(args, **kwargs)
        p.datecreated = datetime.datetime.now(datetime.timezone.utc)

        rec = p.buildrec()
        rec["moniker"] = playermoniker
        rec["membermoniker"] = p.membermoniker
        rec["datecreated"] = datetime.datetime.now(datetime.timezone.utc)
        io.echo(f"mm.player.create.110: {rec=}", level="debug")

        database.upsert(
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
                "module",
                "membermoniker",
                "datelastplayed",
                "datecreated",
            ],
            mogrify=True,
            conn=conn,
        )

        with database.cursor(conn) as cur:
            sql = f"select * from {libmm.SCHEMA}.player where moniker=%s"
            cur.execute(sql, (playermoniker,))
            if cur.rowcount > 0:
                rec = cur.fetchone()
                p = load(args, playermoniker, **kwargs)
                return p

        io.echo("mm.player.create.120: player table corrupted", level="error")
        return False

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
