from bbsengine6 import database, io

from . import lib as libmm

FIELDS = ("kind", "modulepath", "name", "title", "modulepath", "state")


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
        self.title = self.name
        self.table = "murdermotel.item"
        self.pool = kwargs.get("pool", None)

    def short(self) -> str:
        return self.title or f"Item: {self.name}"

    def buildrec(self):
        rec = {}
        for f in FIELDS:
            rec[f] = getattr(self, f)
        return rec

    def save(self, mogrify=False):
        if self.pool is None:
            io.echo(f"mm.item.save.180: {self.pool=}", level="error")
            return False

        i = {}
        for f in FIELDS:
            i[f] = getattr(self, f)

        with database.connect(self.args, pool=self.pool) as conn:
            database.update(
                self.args,
                f"{libmm.SCHEMA}.item",
                self.name,
                i,
                primarykey="name",
                conn=conn,
            )
            conn.commit()
        return True


def load(args, itemname, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            sql = f"select * from {libmm.SCHEMA}.item where name=%s"
            dat = itemname
            cur.execute(sql, dat)
            if cur.rowcount == 0:
                if args.debug is True:
                    io.echo(f"unable to load item {itemname!r}", level="debug")
                    return False

            rec = cur.fetchone()

            r = Item(args, **kwargs)
            for f in FIELDS:
                setattr(r, f, rec[f])

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


def getcount(args, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            sql = f"select count(*) from {libmm.SCHEMA}.item"
            cur.execute(sql)
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
