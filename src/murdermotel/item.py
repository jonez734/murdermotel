from bbsengine6 import database, io

from . import lib as libmm

FIELDS = ("kind", "modulepath", "name", "serial", "title", "state")


def init(args, obj=None, room=None, **kwargs) -> bool:
    return True


def access(args, op, **kwargs) -> bool:
    return op in ("init", "run", "turn")


def buildargs(args, obj=None, room=None, **kwargs):
    return None


def main(args, **kwargs) -> bool:
    return True


class Item(object):
    def __init__(self, args, **kwargs):
        self.args = args
        self.kind = "item"
        self.modulepath = "item"
        self.name = "name"
        self.serial = kwargs.get("serial", 0)
        self.title = self.name
        self.table = "murdermotel.item"
        self.pool = kwargs.get("pool", None)

    def __str__(self) -> str:
        return self.short()

    def short(self) -> str:
        return self.title or f"Item: {self.name}"

    def buildrec(self):
        rec = {}
        for f in FIELDS:
            rec[f] = getattr(self, f)
        return rec

    def save(self, mogrify=False, **kwargs):
        def _work(conn):
            i = {}
            for f in FIELDS:
                i[f] = getattr(self, f)

            if not database.upsert(
                self.args,
                f"{libmm.SCHEMA}.item",
                i,
                conflict_columns=["name"],
                mogrify=mogrify,
                conn=conn,
            ):
                io.echo("mm.item.save.105: item upsert failed", level="error")
                return False
            return True

        conn = kwargs.get("conn", None)
        if conn is None:
            if self.pool is None:
                io.echo(f"mm.item.save.180: {self.pool=}", level="error")
                return False
            with database.connect(self.args, pool=self.pool) as conn:
                result = _work(conn)
                conn.commit()
                return result
        else:
            return _work(conn)


def load(args, itemname, serial: int = 0, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query("SELECT * FROM $murdermotel.item WHERE name = :name", name=itemname)
            cur.execute(q)
            if cur.rowcount == 0:
                if args.debug is True:
                    io.echo(
                        f"unable to load item {itemname!r}",
                        level="debug",
                    )
                    return None

            rec = cur.fetchone()

            r = Item(args, **kwargs)
            for f in FIELDS:
                if f in rec:
                    setattr(r, f, rec[f])
            r.serial = serial
            if "type" in rec:
                r.kind = rec["type"]
            if "module" in rec:
                r.modulepath = rec["module"]

            return r

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.room.load.100: {pool=}", level="error")
            return None
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def getcount(args, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query("SELECT COUNT(*) AS count FROM $murdermotel.item")
            cur.execute(q)
            if cur.rowcount == 0:
                return 0
            row = cur.fetchone()
            count = row.get("count", False)
            io.echo(f"libmm.item.getcount.120: {count=}", level="debug")
            return count

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo("libmm.item.getcount.100: {pool=}", level="error")
            return None
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def build(args, rec: dict, **kwargs) -> Item:
    i = Item(args, **kwargs)
    for f in FIELDS:
        setattr(i, f, rec[f])
    return i
