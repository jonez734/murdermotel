import argparse

from bbsengine6 import database, io

from . import item as libitem, lib as libmm

FIELDS = ("id", "modulepath", "description", "title", "shortname")
EXITS = ("north", "south", "east", "west", "up", "down")


def init(args, obj=None, room=None, **kwargs) -> bool:
    return True


def access(args, op, **kwargs) -> bool:
    return op in ("init", "run", "turn")


def buildargs(args, obj=None, room=None, **kwargs):
    return None


def main(args, **kwargs) -> bool:
    return True


class Room(object):
    args: argparse.Namespace
    modulepath: str | None
    shortname: str | None
    id: int | None
    title: str | None
    description: str | None
    items: list
    exits: dict
    table: str
    pool: object
    north: int | None
    south: int | None
    east: int | None
    west: int | None
    up: int | None
    down: int | None

    def __init__(self, args, **kwargs):
        self.args = args
        self.modulepath = None
        self.shortname = None
        self.id = None
        self.title = None
        self.description = None
        self.items = []
        self.exits = {}
        self.north = None
        self.south = None
        self.east = None
        self.west = None
        self.up = None
        self.down = None
        self.table = "murdermotel.playground"
        self.pool = kwargs.get("pool", None)
        self.fields = ("shortname", "title", "description", "modulepath")

    def on_turn(self, args, room=None, **kwargs):
        io.echo("mm.room.on_turn.100: calling .turn()", level="debug")
        if self.modulepath:
            return libmm.runmodule(
                args, "turn", self.modulepath, obj=self, room=room, **kwargs
            )
        return True

    def short(self) -> str:
        return self.title or f"Room {self.id}" if self.id else "Room"

    def buildrec(self):
        rec = {}
        for f in FIELDS:
            rec[f] = getattr(self, f)
        for f in EXITS:
            rec[f] = getattr(self, f)
        return rec

    def finditem(self, shortname):
        if self.args.debug is True:
            io.echo(
                "Room.finditem.100: items={self.items!r} shortname={shortname}",
                level="debug",
            )
        for x in range(0, len(self.items)):
            if (
                self.items[x].name.lower() == shortname.lower()
                or self.items[x].title.lower() == shortname.lower()
            ):
                return x
        return None

    def save(self, mogrify=False, **kwargs):
        def _work(conn):
            r = {}
            for f in FIELDS:
                r[f] = getattr(self, f)
            for e in EXITS:
                r[e] = self.exits[e]

            if not database.upsert(
                self.args,
                f"{libmm.SCHEMA}.playground",
                r,
                conflict_columns=["id"],
                mogrify=mogrify,
                conn=conn,
            ):
                io.echo("mm.room.save.105: room upsert failed", level="error")
                return False

            with database.cursor(conn) as cur:
                params = {"roomid": self.id}
                q = database.query(
                    "DELETE FROM $murdermotel.map_item_room WHERE roomid = :roomid",
                    **params,
                )
                cur.execute(q, params)
                for i in self.items:
                    m = {}
                    m["itemname"] = i.name
                    m["serial"] = i.serial
                    m["roomid"] = self.id
                    if not database.upsert(
                        self.args,
                        "murdermotel.map_item_room",
                        m,
                        conflict_columns=["itemname", "serial", "roomid"],
                        mogrify=mogrify,
                        conn=conn,
                    ):
                        io.echo("mm.room.save.110: item upsert failed", level="error")
                        return False
            return True

        conn = kwargs.get("conn", None)
        if conn is None:
            if self.pool is None:
                io.echo(f"mm.room.save.180: {self.pool=}", level="error")
                return False
            with database.connect(self.args, pool=self.pool) as conn:
                result = _work(conn)
                conn.commit()
                return result
        else:
            return _work(conn)


def load(args, roomid, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            params = {"roomid": roomid}
            q = database.query(
                "SELECT * FROM $murdermotel.playground WHERE id = :roomid OR shortname = :roomid::text",
                **params,
            )
            cur.execute(q, params)
            if cur.rowcount == 0:
                if args.debug is True:
                    io.echo(f"unable to load room {roomid=}", level="error")
                    return False

            rec = cur.fetchone()
            if rec is None:
                io.echo(
                    f"room {roomid} does not exist. Use 'lrooms' or 'arooms' to list available rooms.",
                    level="error",
                )
                return False

            r = Room(args, **kwargs)
            for f in FIELDS:
                setattr(r, f, rec.get(f))
            r.items = getitems(args, r.id, **kwargs)
            for f in EXITS:
                r.exits[f] = rec.get(f)

            return r

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.room.load.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


# @since 20220921
def getitems(args, roomid, **kwargs) -> list:
    def _work(conn) -> list:
        items: list = []
        with database.cursor(conn) as cur:
            params = {"roomid": roomid}
            q = database.query(
                "SELECT m.itemname, m.serial, i.title, i.kind, i.usemessages FROM $murdermotel.item i JOIN $murdermotel.map_item_room m ON m.itemname = i.name AND m.serial = i.serial WHERE m.roomid = :roomid",
                **params,
            )
            cur.execute(q, params)

            if cur.rowcount == 0:
                return []

            for rec in cur.fetchall():
                i = libitem.Item(args, serial=rec.get("serial"))
                i.name = rec["itemname"]
                i.title = rec["title"]
                i.kind = rec["kind"]
                i.usemessages = rec["usemessages"] if "usemessages" in rec else []
                items.append(i)
        return items

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.room.getitems.100: {pool=}", level="error")
            return []
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def getcount(args, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query("SELECT COUNT(*) AS count FROM $murdermotel.playground")
            cur.execute(q)
            if cur.rowcount == 0:
                return 0
            row = cur.fetchone()
            count = row.get("count", False)
            io.echo(f"libmm.room.getcount.120: {count=}", level="debug")
            return count

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"libmm.room.getcount.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def build(args, rec: dict, **kwargs) -> Room:
    r = Room(args, **kwargs)
    for f in FIELDS:
        setattr(r, f, rec[f])
    for e in EXITS:
        r.exits[e] = rec[e]
    return r
