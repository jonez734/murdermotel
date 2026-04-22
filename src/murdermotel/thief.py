import random
import random as randomlib

from bbsengine6 import database, io, util

from . import lib as libmm
from . import room as libroom
from .obj import Living, registry


THIEF_NAME = "thief"
THIEF_HEALTH = 35
SCHEMA = "murdermotel"


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

    def short(self) -> str:
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
                "murdermotel.thief.main.100: player does not exist",
                logger_name="murdermotel",
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

        pool = kwargs.get("pool", None)
        conn = kwargs.get("conn", None)
        if conn is None and pool is not None:
            with database.connect(self.args, pool=pool) as conn:
                self.save(conn=conn)
                player.save(conn=conn)
                conn.commit()
        else:
            if self.pool:
                self.save(conn=conn) if conn else self.save()
            player.save(conn=conn) if conn else player.save()
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
                q = database.query(
                    "DELETE FROM $murdermotel.map_item_thief WHERE thiefname = :thiefname",
                    thiefname=self.name,
                )
                cur.execute(q)

                for i in self.items:
                    m = {}
                    m["itemname"] = i.name
                    m["serial"] = i.serial
                    m["thiefname"] = self.name
                    if not database.insert(
                        self.args,
                        f"{SCHEMA}.map_item_thief",
                        m,
                        returnid=False,
                        mogrify=True,
                        conn=conn,
                    ):
                        io.echo("mm.Thief.save.110: insert failed", level="error")
                        return False
            return True

        conn = kwargs.get("conn", None) or self.conn
        if conn is None:
            if self.pool is None:
                io.echo(f"mm.Thief.save.100: {self.pool=}", level="error")
                return False
            with database.connect(self.args, pool=self.pool) as conn:
                result = _work(conn)
                conn.commit()
                return result
        else:
            return _work(conn)


def access(args, op, **kwargs) -> bool:
    return op in ("init", "run", "turn")


def init(args, obj=None, room=None, **kwargs) -> bool:
    return True


def buildargs(args, obj=None, room=None, **kwargs):
    return None


def main(args, **kwargs) -> bool:
    return True


def load(args, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT name FROM $murdermotel.npc WHERE name = :name", name=THIEF_NAME
            )
            cur.execute(q)
            npc_exists = cur.rowcount > 0
            if npc_exists:
                io.echo("mm.thief.load.090: npc record exists", level="debug")

        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT * FROM $murdermotel.thief WHERE name = :name", name=THIEF_NAME
            )
            cur.execute(q)
            if cur.rowcount == 0:
                if npc_exists:
                    io.echo(
                        "mm.thief.load.100: npc exists but thief table empty, "
                        "skipping create",
                        level="debug",
                    )
                    return None
                io.echo("mm.thief.load.110: no thief found, can create", level="debug")
                return None

            rec = cur.fetchone()
            t = build(args, rec, **kwargs)
            t.items = getitems(args, **kwargs)
            return t

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.thief.load.120: {pool=}", level="error")
            return None
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def save(args, thief, **kwargs):
    def _work(conn):
        rec = thief.buildrec()
        database.update(
            args,
            f"{libmm.SCHEMA}.thief",
            THIEF_NAME,
            rec,
            primarykey="name",
            conn=conn,
        )

        with database.cursor(conn) as cur:
            q = database.query(
                "DELETE FROM $murdermotel.map_item_thief WHERE thiefname = :thiefname",
                thiefname=THIEF_NAME,
            )
            cur.execute(q)

            for i in thief.items:
                m = {}
                m["itemname"] = i.name
                m["thiefname"] = THIEF_NAME
                if not database.insert(
                    args,
                    f"{libmm.SCHEMA}.map_item_thief",
                    m,
                    returnid=False,
                    mogrify=True,
                    conn=conn,
                ):
                    io.echo("mm.thief.save.110: insert failed", level="error")
                    return False
        return True

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.thief.save.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            _work(conn)
    else:
        _work(conn)
    return True


def create(args, **kwargs):
    pool = kwargs.get("pool", None)
    if pool is None:
        io.echo(f"mm.thief.create.100: {pool=}", level="error")
        return False

    def _work(conn):
        t = build(
            args,
            {"name": THIEF_NAME, "bag": [], "roomid": 10, "healthpoints": THIEF_HEALTH},
            **kwargs,
        )

        rec = t.buildrec()
        io.echo(f"mm.thief.create.110: {rec=}", level="debug")

        if not database.upsert(
            args,
            f"{libmm.SCHEMA}.thief",
            rec,
            conflict_columns=["name"],
            update_columns=["bag", "roomid", "healthpoints"],
            mogrify=True,
            conn=conn,
        ):
            io.echo("mm.thief.create.115: upsert failed", level="error")
            return False

        with database.cursor(conn) as cur:
            q = database.query(
                """
                INSERT INTO $murdermotel.npc (name, kind, modulepath, title)
                VALUES (:name, :kind, :modulepath, :title)
                ON CONFLICT (name) DO NOTHING
            """,
                name=THIEF_NAME,
                kind="thief",
                modulepath="thief",
                title="The Thief",
            )
            cur.execute(q)

        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT * FROM $murdermotel.thief WHERE name = :name", name=THIEF_NAME
            )
            cur.execute(q)
            if cur.rowcount > 0:
                rec = cur.fetchone()
                t = build(args, rec, **kwargs)
                t.items = getitems(args, **kwargs)
                return t

        io.echo("mm.thief.create.120: thief table corrupted", level="error")
        return False

    try:
        conn = kwargs.get("conn", None)
        if conn is None:
            pool = kwargs.get("pool", None)
            if pool is None:
                io.echo(f"mm.thief.create.140: {pool=}", level="error")
                return False
            with database.connect(args, pool=pool) as conn:
                return _work(conn)
        else:
            return _work(conn)
    except Exception:
        io.echo_traceback("mm.thief.create.160")
        raise


def getitems(args, **kwargs):
    def _work(conn):
        items = []
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT itemname, serial FROM $murdermotel.map_item_thief WHERE thiefname = :name",
                name=THIEF_NAME,
            )
            cur.execute(q)
            if cur.rowcount == 0:
                return items
            res = cur.fetchmany()
            for rec in res:
                from . import item as libitem

                item = libitem.load(args, rec["itemname"], serial=rec.get("serial"))
                if item is None:
                    io.echo(f"mm.thief.getitems: {item=}", level="error")
                    break
                items.append(item)
            return items

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.thief.getitems.100: {pool=}", level="error")
            return []
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def exists(args, **kwargs) -> bool:
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT name FROM $murdermotel.thief WHERE name = :name",
                name=THIEF_NAME,
            )
            cur.execute(q)
            if cur.rowcount == 0:
                return False
            return True

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.thief.exists.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def build(args, rec, **kwargs):
    pool = kwargs.get("pool", None)
    t = Thief(args, pool=pool)
    t.name = rec.get("name", THIEF_NAME)
    t.bag = rec.get("bag", [])
    t.roomid = rec.get("roomid", 10)
    t.healthpoints = rec.get("healthpoints", THIEF_HEALTH)
    return t


def turn(args, **kwargs) -> bool:
    obj = kwargs.get("obj")
    player = kwargs.get("player", None)
    if player is None:
        io.echo("You do not exist! Go Away!")
        util.logentry(
            "murdermotel.thief.main.100: player does not exist",
            logger_name="murdermotel",
        )
        return False

    if obj is None:
        io.echo("The thief does not exist!")
        util.logentry(
            "murdermotel.thief.main.120: thief does not exist",
            logger_name="murdermotel",
        )
        return False

    io.echo("THIEF! THIEF!  You were ATTACKED!")
    player.moves -= 5

    if util.diceroll(10) < 4:
        stolen = steal_from_player(player, obj, **kwargs)
        if stolen:
            io.echo(f"The thief stole {stolen.name} from you!")

    pool = kwargs.get("pool", None)
    conn = kwargs.get("conn", None)
    if conn is None and pool is not None:
        with database.connect(args, pool=pool) as conn:
            obj.save(conn=conn)
            player.save(conn=conn)
            conn.commit()
    else:
        if pool:
            obj.save(conn=conn) if conn else obj.save()
        player.save(conn=conn) if conn else player.save()
    return True


def steal_from_player(player, thief, **kwargs):
    if not player.items:
        return None

    idx = randomlib.randint(0, len(player.items) - 1)
    item = player.items.pop(idx)
    thief.items.append(item)

    args = kwargs.get("args", None)
    pool = kwargs.get("pool", None)
    conn = kwargs.get("conn", None)
    if conn is None and pool is not None:
        with database.connect(args, pool=pool) as conn:
            player.save(conn=conn)
            thief.save(conn=conn)
            conn.commit()
    else:
        if pool and args:
            player.save(conn=conn) if conn else player.save()
            thief.save(conn=conn) if conn else thief.save()

    return item
