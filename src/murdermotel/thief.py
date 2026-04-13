import random as randomlib

from bbsengine6 import database, io, util

from . import lib as libmm


THIEF_NAME = "thief"
THIEF_HEALTH = 35


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
            sql = f"select name from {libmm.SCHEMA}.npc where name=%s"
            dat = (THIEF_NAME,)
            cur.execute(sql, dat)
            npc_exists = cur.rowcount > 0
            if npc_exists:
                io.echo("mm.thief.load.090: npc record exists", level="debug")

        with database.cursor(conn) as cur:
            sql = f"select * from {libmm.SCHEMA}.thief where name=%s"
            dat = (THIEF_NAME,)
            cur.execute(sql, dat)
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
            sql = f"delete from {libmm.SCHEMA}.map_item_thief where thiefname=%s"
            dat = (THIEF_NAME,)
            cur.execute(sql, dat)

            for i in thief.items:
                m = {}
                m["itemname"] = i.name
                m["thiefname"] = THIEF_NAME
                database.insert(
                    args,
                    f"{libmm.SCHEMA}.map_item_thief",
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

        database.upsert(
            args,
            f"{libmm.SCHEMA}.thief",
            rec,
            conflict_columns=["name"],
            update_columns=["bag", "roomid", "healthpoints"],
            mogrify=True,
            conn=conn,
        )

        with database.cursor(conn) as cur:
            sql = f"""INSERT INTO {libmm.SCHEMA}.npc (name, kind, module, title)
                      VALUES (%s, %s, %s, %s)
                      ON CONFLICT (name) DO NOTHING"""
            dat = (THIEF_NAME, "thief", "thief", "The Thief")
            cur.execute(sql, dat)

        with database.cursor(conn) as cur:
            sql = f"select * from {libmm.SCHEMA}.thief where name=%s"
            cur.execute(sql, (THIEF_NAME,))
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
            sql = f"select * from {libmm.SCHEMA}.map_item_thief where thiefname=%s"
            dat = (THIEF_NAME,)
            cur.execute(sql, dat)
            if cur.rowcount == 0:
                return items
            res = cur.fetchmany()
            for rec in res:
                from . import item as libitem

                item = libitem.load(args, rec["itemname"])
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
            sql = f"select name from {libmm.SCHEMA}.thief where name=%s"
            dat = (THIEF_NAME,)
            cur.execute(sql, dat)
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
    t = libmm.Thief(args, pool=pool)
    t.name = rec.get("name", THIEF_NAME)
    t.bag = rec.get("bag", [])
    t.roomid = rec.get("roomid", 10)
    t.healthpoints = rec.get("healthpoints", THIEF_HEALTH)
    return t


def turn(args, obj=None, room=None, **kwargs) -> bool:
    player = kwargs.get("player", None)
    if player is None:
        io.echo("You do not exist! Go Away!")
        util.logentry(
            "murdermotel.thief.main.100: player does not exist", prg="murdermotel"
        )
        return False

    if obj is None:
        io.echo("The thief does not exist!")
        util.logentry(
            "murdermotel.thief.main.120: thief does not exist", prg="murdermotel"
        )
        return False

    io.echo("THIEF! THIEF!  You were ATTACKED!")
    player.moves -= 5

    if util.diceroll(10) < 4:
        stolen = steal_from_player(player, obj, **kwargs)
        if stolen:
            io.echo(f"The thief stole {stolen.name} from you!")

    pool = kwargs.get("pool", None)
    if pool:
        obj.save()

    player.save()
    return True


def steal_from_player(player, thief, **kwargs):
    if not player.items:
        return None

    idx = randomlib.randint(0, len(player.items) - 1)
    item = player.items.pop(idx)
    thief.items.append(item)

    args = kwargs.get("args", None)
    pool = kwargs.get("pool", None)
    if pool and args:
        player.save()
        thief.save()

    return item
