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
    def __init__(self, args, **kwargs):
        self.args = args
        self.modulepath = None
        self.shortname = None
        self.id = None
        self.title = None
        self.items = []
        self.exits = {}
        self.table = "murdermotel.playground"
        self.pool = kwargs.get("pool", None)
        self.fields = ("shortname", "title", "description", "modulepath")

    def on_turn(self, args, room=None, **kwargs):
        io.echo(f"mm.room.on_turn.100: calling .turn()", level="debug")
        if self.modulepath:
            return libmm.runmodule(args, self, "turn", room=room, **kwargs)
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
            if self.items[x].name == shortname:
                return x
        return None

    def save(self, mogrify=False):
        if self.pool is None:
            io.echo(f"mm.room.save.180: {self.pool=}", level="error")
            return False

        r = {}
        for f in FIELDS:
            r[f] = getattr(self, f)

        for e in EXITS:
            r[e] = self.exits[e]

        with database.connect(self.args, pool=self.pool) as conn:
            database.update(
                self.args,
                f"{libmm.SCHEMA}.playground",
                self.id,
                r,
                primarykey="id",
                mogrify=mogrify,
                pool=self.pool,
            )
            with database.cursor(conn) as cur:
                sql = "delete from murdermotel.map_item_room where roomid=%s"
                dat = (self.id,)
                cur.execute(sql, dat)
                for i in self.items:
                    m = {}
                    m["itemname"] = i.name
                    m["roomid"] = self.id
                    database.insert(
                        self.args,
                        "murdermotel.map_item_room",
                        m,
                        returnid=False,
                        mogrify=mogrify,
                    )

            conn.commit()
        return True


def load(args, roomid, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            sql = f"select * from {libmm.SCHEMA}.playground where id=%s or shortname=%s::text"
            dat = (roomid, roomid)
            cur.execute(sql, dat)
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
def getitems(args, roomid, **kwargs):
    def _work(conn):
        items = []
        with database.cursor(conn) as cur:
            sql = "select * from murdermotel.item as i, murdermotel.map_item_room as m where (m.roomid=%s) and m.itemname=i.name"
            dat = (roomid,)
            cur.execute(sql, dat)

            if cur.rowcount == 0:
                return []

            for rec in database.resultiter(cur):
                i = libitem.Item(args)
                i.name = rec["name"]
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
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def getcount(args, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            sql = f"select count(*) from {libmm.SCHEMA}.playground"
            cur.execute(sql)
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
