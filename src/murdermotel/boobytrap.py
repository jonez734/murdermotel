import random as randomlib

from bbsengine6 import database, io, util

from . import lib as libmm


BOOBYTRAP_NAME = "boobytrap"
BOOBYTRAP_HEALTH = 20


def access(args, op, **kwargs) -> bool:
    return op in ("init", "run", "turn")


def init(args, obj=None, room=None, **kwargs) -> bool:
    return True


def buildargs(args, obj=None, room=None, **kwargs):
    return None


def main(args, **kwargs):
    return True


class Item:
    module: str = None

    def __init__(self, args):
        super().__init__()
        self.roomid = None

    def on_turn(self, args, room=None, **kwargs) -> bool:
        return True

    def short(self):
        return "NEEDINFO.item"


class BoobyTrap(Item):
    def __init__(self, args, **kwargs):
        super().__init__(args)
        self.args = args
        self.name = "boobytrap"
        self.healthpoints = 20
        self.running = False
        self.timer = 0
        self.playerid = None
        self.kind = "boobytrap"
        self.modulepath = "boobytrap"

        self.conn = kwargs.get("conn", None)
        self.pool = kwargs.get("pool", None)

        loaded = kwargs.get("loaded_boobytrap", None)
        if loaded:
            self.roomid = loaded.roomid
            self.running = loaded.running
            self.timer = loaded.timer
        else:
            self.roomid = randomlib.randint(10, 140 - 10 + 1)

        libmm.registry.register(self)

    def short(self):
        return ":mousetrap: Booby-Trap"

    def buildrec(self, **kwargs):
        rec = {}
        rec["name"] = self.name
        rec["running"] = self.running
        rec["timer"] = self.timer
        return rec

    def on_turn(self, args, room=None, **kwargs) -> bool:
        player = kwargs.get("player", None)
        in_same_room = player is not None and player.roomid == self.roomid

        if self.running:
            self.timer -= 1
            if self.timer <= 0:
                if in_same_room:
                    io.echo("The boobytrap is triggered! It goes SNAP!")
                    if player:
                        player.moves -= 10
                        player.save()
                self.running = False
                self.timer = 0
        elif in_same_room:
            io.echo("There's a boobytrap here. It looks inactive.")
            if (
                io.inputboolean(
                    "{var:promptcolor}Set the trap? [yN]: {var:inputcolor}", "N"
                )
                is True
            ):
                self.running = True
                self.timer = 3
                io.echo("You set the boobytrap!")

        if self.pool:
            self.save()

        return True

    def save(self, **kwargs) -> bool:
        def _work(conn):
            rec = self.buildrec()
            database.update(
                self.args,
                f"{libmm.SCHEMA}.boobytrap",
                self.name,
                rec,
                primarykey="name",
                conn=conn,
            )

            with database.cursor(conn) as cur:
                sql = f"delete from {libmm.SCHEMA}.map_item_room where itemname=%s"
                dat = (self.name,)
                cur.execute(sql, dat)

                m = {}
                m["itemname"] = self.name
                m["roomid"] = self.roomid
                database.insert(
                    self.args,
                    f"{libmm.SCHEMA}.map_item_room",
                    m,
                    returnid=False,
                    mogrify=True,
                    conn=conn,
                )
            return True

        conn = kwargs.get("conn", None) or self.conn
        if conn is None:
            if self.pool is None:
                io.echo(f"mm.BoobyTrap.save.100: {self.pool=}", level="error")
                return False
            with database.connect(self.args, pool=self.pool) as conn:
                _work(conn)
        else:
            _work(conn)
        return True


def load(args, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            sql = f"select * from {libmm.SCHEMA}.boobytrap where name=%s"
            dat = (BOOBYTRAP_NAME,)
            cur.execute(sql, dat)
            if cur.rowcount == 0:
                io.echo(
                    "mm.boobytrap.load.100: no boobytrap found, creating one",
                    level="debug",
                )
                return None

            rec = cur.fetchone()

            roomid = get_room_for_boobytrap(args, conn=conn, **kwargs)

            b = build(args, rec, roomid=roomid, **kwargs)
            return b

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.boobytrap.load.120: {pool=}", level="error")
            return None
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def get_room_for_boobytrap(args, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            sql = f"select roomid from {libmm.SCHEMA}.map_item_room where itemname=%s"
            dat = (BOOBYTRAP_NAME,)
            cur.execute(sql, dat)
            if cur.rowcount == 0:
                return None
            rec = cur.fetchone()
            return rec["roomid"]

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.boobytrap.get_room_for_boobytrap.100: {pool=}", level="error")
            return None
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def save(args, boobytrap, **kwargs):
    def _work(conn):
        rec = boobytrap.buildrec()
        database.update(
            args,
            f"{libmm.SCHEMA}.boobytrap",
            BOOBYTRAP_NAME,
            rec,
            primarykey="name",
            conn=conn,
        )

        with database.cursor(conn) as cur:
            sql = f"delete from {libmm.SCHEMA}.map_item_room where itemname=%s"
            dat = (BOOBYTRAP_NAME,)
            cur.execute(sql, dat)

            m = {}
            m["itemname"] = BOOBYTRAP_NAME
            m["roomid"] = boobytrap.roomid
            database.insert(
                args,
                f"{libmm.SCHEMA}.map_item_room",
                m,
                returnid=False,
                mogrify=True,
                conn=conn,
            )
        return True

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.boobytrap.save.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            _work(conn)
    else:
        _work(conn)
    return True


def create(args, **kwargs):
    pool = kwargs.get("pool", None)
    if pool is None:
        io.echo(f"mm.boobytrap.create.100: {pool=}", level="error")
        return False

    def _work(conn):
        b = build(
            args, {"name": BOOBYTRAP_NAME, "running": False, "timer": 0}, **kwargs
        )

        rec = b.buildrec()
        io.echo(f"mm.boobytrap.create.110: {rec=}", level="debug")

        database.upsert(
            args,
            f"{libmm.SCHEMA}.boobytrap",
            rec,
            conflict_columns=["name"],
            update_columns=["running", "timer"],
            mogrify=True,
            conn=conn,
        )

        with database.cursor(conn) as cur:
            sql = f"select * from {libmm.SCHEMA}.boobytrap where name=%s"
            cur.execute(sql, (BOOBYTRAP_NAME,))
            if cur.rowcount > 0:
                rec = cur.fetchone()
                b = build(args, rec, **kwargs)
                return b

        io.echo("mm.boobytrap.create.120: boobytrap table corrupted", level="error")
        return False

    try:
        conn = kwargs.get("conn", None)
        if conn is None:
            pool = kwargs.get("pool", None)
            if pool is None:
                io.echo(f"mm.boobytrap.create.140: {pool=}", level="error")
                return False
            with database.connect(args, pool=pool) as conn:
                return _work(conn)
        else:
            return _work(conn)
    except Exception:
        io.echo_traceback("mm.boobytrap.create.160")
        raise


def exists(args, **kwargs) -> bool:
    def _work(conn):
        with database.cursor(conn) as cur:
            sql = f"select name from {libmm.SCHEMA}.boobytrap where name=%s"
            dat = (BOOBYTRAP_NAME,)
            cur.execute(sql, dat)
            if cur.rowcount == 0:
                return False
            return True

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.boobytrap.exists.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def build(args, rec, **kwargs):
    pool = kwargs.get("pool", None)
    roomid = kwargs.get("roomid", None)
    b = BoobyTrap(args, pool=pool)
    b.name = rec.get("name", BOOBYTRAP_NAME)
    b.running = rec.get("running", False)
    b.timer = rec.get("timer", 0)
    if roomid is not None:
        b.roomid = roomid
    return b


def turn(args, **kwargs) -> bool:
    obj = kwargs.get("obj")
    if obj is None:
        io.echo("The boobytrap does not exist!")
        util.logentry(
            "murdermotel.boobytrap.turn.100: boobytrap does not exist",
            logger_name="murdermotel",
        )
        return False

    player = kwargs.get("player", None)
    in_same_room = player is not None and player.roomid == obj.roomid

    if obj.running:
        obj.timer -= 1
        if obj.timer <= 0:
            if in_same_room:
                io.echo("The boobytrap is triggered! It goes SNAP!")
                if player:
                    player.moves -= 10
                    player.save()
            obj.running = False
            obj.timer = 0
    elif in_same_room:
        io.echo("There's a boobytrap here. It looks inactive.")
        if (
            io.inputboolean(
                "{var:promptcolor}Set the trap? [yN]: {var:inputcolor}", "N"
            )
            is True
        ):
            obj.running = True
            obj.timer = 3
            io.echo("You set the boobytrap!")

    pool = kwargs.get("pool", None)
    if pool:
        obj.save()

    return True
