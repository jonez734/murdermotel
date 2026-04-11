import random as randomlib

from bbsengine6 import database, io, util

from . import lib as libmm


BOOBYTRAP_NAME = "boobytrap"
BOOBYTRAP_HEALTH = 20


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
        io.echo(f"mm.boobytrap.create.120: {rec=}", level="debug")

        database.insert(
            args,
            f"{libmm.SCHEMA}.boobytrap",
            rec,
            primarykey="name",
            mogrify=True,
            conn=conn,
        )

        with database.cursor(conn) as cur:
            sql = f"insert into {libmm.SCHEMA}.npc (name, kind, module, title) values (%s, %s, %s, %s)"
            dat = (BOOBYTRAP_NAME, "boobytrap", "boobytrap", "Booby Trap")
            cur.execute(sql, dat)

        roomid = randomlib.randint(10, 140 - 10 + 1)
        b.roomid = roomid

        m = {}
        m["itemname"] = BOOBYTRAP_NAME
        m["roomid"] = roomid
        database.insert(
            args,
            f"{libmm.SCHEMA}.map_item_room",
            m,
            returnid=False,
            mogrify=True,
            conn=conn,
        )

        return b

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
    b = libmm.BoobyTrap(args, pool=pool)
    b.name = rec.get("name", BOOBYTRAP_NAME)
    b.running = rec.get("running", False)
    b.timer = rec.get("timer", 0)
    if roomid is not None:
        b.roomid = roomid
    return b


def turn(args, **kwargs):
    boobytrap = kwargs.get("boobytrap", None)
    if boobytrap is None:
        io.echo("The boobytrap does not exist!")
        util.logentry(
            "murdermotel.boobytrap.turn.100: boobytrap does not exist",
            prg="murdermotel",
        )
        return False

    player = kwargs.get("player", None)
    in_same_room = player is not None and player.roomid == boobytrap.roomid

    if boobytrap.running:
        boobytrap.timer -= 1
        if boobytrap.timer <= 0:
            if in_same_room:
                io.echo("The boobytrap is triggered! It goes SNAP!")
                if player:
                    player.moves -= 10
                    player.save()
            boobytrap.running = False
            boobytrap.timer = 0
    elif in_same_room:
        io.echo("There's a boobytrap here. It looks inactive.")
        if (
            io.inputboolean(
                "{var:promptcolor}Set the trap? [yN]: {var:inputcolor}", "N"
            )
            is True
        ):
            boobytrap.running = True
            boobytrap.timer = 3
            io.echo("You set the boobytrap!")

    pool = kwargs.get("pool", None)
    if pool:
        boobytrap.save()

    return True
