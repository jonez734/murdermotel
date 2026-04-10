import random as randomlib

from bbsengine6 import database, io, util

from . import lib as libmm


WOLF_NAME = "wolf"
WOLF_HEALTH = 35
WOLF_AUTO_ATTACK_CHANCE = 6


def init(args, **kw):
    return True


def access(args, op, **kw):
    return True


def buildargs(args=None, **kw):
    return None


def load(args, **kwargs):
    def _work(conn):
        with database.cursor(conn) as cur:
            sql = f"select * from {libmm.SCHEMA}.wolf where name=%s"
            dat = (WOLF_NAME,)
            cur.execute(sql, dat)
            if cur.rowcount == 0:
                io.echo("mm.rabidwolf.load.100: no wolf found, creating one", level="debug")
                return None

            rec = cur.fetchone()
            w = build(args, rec, **kwargs)
            return w

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.rabidwolf.load.120: {pool=}", level="error")
            return None
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def save(args, wolf, **kwargs):
    def _work(conn):
        rec = wolf.buildrec()
        database.update(
            args,
            f"{libmm.SCHEMA}.wolf",
            WOLF_NAME,
            rec,
            primarykey="name",
            conn=conn,
        )
        return True

    pool = kwargs.get("pool", None)
    if pool is None:
        io.echo(f"mm.rabidwolf.save.100: {pool=}", level="error")
        return False

    with database.connect(args, pool=pool) as conn:
        _work(conn)
        conn.commit()
    return True


def create(args, **kwargs):
    pool = kwargs.get("pool", None)
    if pool is None:
        io.echo(f"mm.rabidwolf.create.100: {pool=}", level="error")
        return False

    def _work(conn):
        w = build(args, {"name": WOLF_NAME, "roomid": 10, "healthpoints": WOLF_HEALTH}, **kwargs)

        rec = w.buildrec()
        io.echo(f"mm.rabidwolf.create.120: {rec=}", level="debug")

        database.insert(
            args,
            f"{libmm.SCHEMA}.wolf",
            rec,
            primarykey="name",
            mogrify=True,
            conn=conn,
        )

        with database.cursor(conn) as cur:
            sql = f"insert into {libmm.SCHEMA}.npc (name, kind, module, title) values (%s, %s, %s, %s)"
            dat = (WOLF_NAME, "wolf", "rabidwolf", "The Rabid Wolf")
            cur.execute(sql, dat)

        return w

    try:
        conn = kwargs.get("conn", None)
        if conn is None:
            pool = kwargs.get("pool", None)
            if pool is None:
                io.echo(f"mm.rabidwolf.create.140: {pool=}", level="error")
                return False
            with database.connect(args, pool=pool) as conn:
                return _work(conn)
        else:
            return _work(conn)
    except Exception:
        io.echo_traceback("mm.rabidwolf.create.160")
        raise


def exists(args, **kwargs) -> bool:
    def _work(conn):
        with database.cursor(conn) as cur:
            sql = f"select name from {libmm.SCHEMA}.wolf where name=%s"
            dat = (WOLF_NAME,)
            cur.execute(sql, dat)
            if cur.rowcount == 0:
                return False
            return True

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.rabidwolf.exists.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def build(args, rec, **kwargs):
    pool = kwargs.get("pool", None)
    w = libmm.RabidWolf(args, pool=pool)
    w.name = rec.get("name", WOLF_NAME)
    w.roomid = rec.get("roomid", 10)
    w.healthpoints = rec.get("healthpoints", WOLF_HEALTH)
    return w


def wolf_attack_player(args, player, wolf, **kwargs):
    damage = randomlib.randint(1, 10) + 10
    io.echo(f"damage={damage}", level="debug")
    io.echo(
        "The {} claws you for {}".format(
            wolf.short(), util.pluralize(damage, "move", "moves")
        )
    )
    player.moves -= damage
    if player.moves < 0:
        player.moves = 0
        io.echo("You are out of moves. You are dead.")

    player.save()


def turn(args, **kwargs):
    player = kwargs.get("player", None)
    if player is None:
        io.echo("You do not exist! Go Away!")
        util.logentry(
            "murdermotel.rabidwolf.turn.100: player does not exist", prg="murdermotel"
        )
        return False

    wolf = kwargs.get("wolf", None)
    if wolf is None:
        io.echo("The wolf does not exist!")
        util.logentry(
            "murdermotel.rabidwolf.turn.120: wolf does not exist", prg="murdermotel"
        )
        return False

    attacked = kwargs.get("attacked", False)
    ignored = kwargs.get("ignored", False)

    if attacked:
        if util.diceroll(10) < WOLF_AUTO_ATTACK_CHANCE:
            wolf_attack_player(args, player, wolf, **kwargs)

    if ignored:
        if util.diceroll(10) < WOLF_AUTO_ATTACK_CHANCE:
            io.echo(f"The {wolf.short()} attacks you!")
            wolf_attack_player(args, player, wolf, **kwargs)

    pool = kwargs.get("pool", None)
    if pool:
        save(args, wolf, pool=pool)

    return True


def help(**kw):
    player = kw["player"] if "player" in kw else None

    if player is None:
        io.echo("You do not exist! Go Away!", level="error")
        return False

    if len(player.weapons()) > 0:
        io.echo("{f6}{var:optioncolor}[A]{var:labelcolor}ttack")
    io.echo(
        "{var:optioncolor}[I]{var:labelcolor}gnore{f6}{var:optioncolor}[F]{var:labelcolor}lee room{f6}"
    )
    return


def attack(args, player, weapons, wolf, **kwargs):
    io.echo(f"weapons={weapons!r}", level="debug")
    weapon = None
    if len(weapons) == 1:
        io.echo(f"you only have 1 weapon: {weapons[0]}")
        weapon = weapons[0]
    else:
        key = 0
        buf = []
        options = ""
        for w in weapons:
            buf.append(f"{chr(ord('1') + key)}) {w}")
            options += chr(ord("1") + key)
            key += 1
        ch = io.inputchar(
            f"{{var:promptcolor}}kill with? {' '.join(buf)} {{var:inputcolor}}",
            options,
            "",
        )
        weapon = weapons[ord(ch) - ord("1")]
        io.echo(f"{ch} {{var:sepcolor}}- {{var:labelcolor}}{weapon}")

    io.echo(f"{wolf=}", level="debug")
    damage = util.diceroll(6) * 5
    io.echo(f"You remove {damage}% of the {wolf.short()}'s strength!")
    player.moves += 5
    wolf.healthpoints -= damage
    if wolf.healthpoints < 0:
        wolf.healthpoints = 0
    if wolf.healthpoints < 1:
        wolf.roomid = 0
        io.echo(f"You killed the {wolf.short()}!")
        player.moves += 500
        util.logentry(f"{player.name} killed the {wolf.short()}!", prg="murdermotel")

    if player.moves < 1:
        io.echo("You have died.")
        player.save()
        return

    player.save()

    pool = kwargs.get("pool", None)
    if pool:
        save(args, wolf, pool=pool)


def flee(args, player, exits):
    io.echo(f"total exits: {len(exits)}", level="debug")
    k = []
    for e in exits.keys():
        k.append(e)

    for t in range(0, len(exits)):
        e = randomlib.choice(k)
        io.echo(f"t={t!r} e={e!r}", level="debug")
        if exits[e] is not None:
            io.echo(f"selected {e!r} exit")
            player.roomid = exits[e]
            player.save()
            break
        io.echo(f"skipped invalid exit {e!r}", level="debug")
    return


def main(args, **kw):
    player = kw["player"] if "player" in kw else None
    if player is None:
        io.echo("You do not exist! Go Away!")
        return False
    wolf = kw["wolf"] if "wolf" in kw else None
    if wolf is None:
        io.echo("The wolf does not exist!")
        return False

    room = kw["room"] if "room" in kw else None
    if room is None:
        io.echo("The room you are in does not exist!")
        return False

    done = False
    while not done:
        libmm.setarea(args, player, "playground: rabid wolf")

        io.echo(f"{{var:labelcolor}}There is a {wolf.short()} snarling at you.{{f6}}")

        weapons = player.weapons()
        options = "IF?"
        if len(weapons) > 0:
            options += "A"
        options = "".join(sorted(options))
        ch = io.inputchar(
            f"{{var:promptcolor}}Make selection {{var:optioncolor}}[{options}]{{var:promptcolor}}: {{var:inputcolor}}",
            options,
            "",
            help=help,
            player=player,
        )
        if ch == "A":
            io.echo(f"Attack {wolf.short()}")
            attack(args, player, weapons, wolf, **kw)
            if wolf.roomid == 0:
                break
            wolf.on_turn(args, room=room, attacked=True, **kw)
            if player.moves < 1:
                break
        elif ch == "I":
            io.echo("Ignore")
            wolf.on_turn(args, room=room, ignored=True, **kw)
            break
        elif ch == "F":
            io.echo("Flee")
            flee(args, player, room.exits)
            break
    return True
