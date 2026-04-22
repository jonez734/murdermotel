import argparse
import random as randomlib
import random
from typing import Any, Optional

from bbsengine6 import database, io, util

from . import lib as libmm
from . import room as libroom
from .obj import Living, registry


WOLF_NAME = "rabidwolf"
WOLF_HEALTH = 35
WOLF_AUTO_ATTACK_CHANCE = 6
SCHEMA = "murdermotel"


class RabidWolf(Living):
    def __init__(self, args, **kwargs):
        super().__init__(args)
        self.name = "wolf"
        self.healthpoints = 35
        self.conn = kwargs.get("conn", None)
        self.pool = kwargs.get("pool", None)
        if self.pool:
            loaded = kwargs.get("loaded_wolf", None)
            if loaded:
                self.roomid = loaded.roomid
                self.healthpoints = loaded.healthpoints
            else:
                self.roomid = random.randint(10, libroom.getcount(args, **kwargs) - 10)
        else:
            self.roomid = random.randint(10, libroom.getcount(args, **kwargs) - 10)
        self.modulepath = None
        registry.register(self)

    def short(self) -> str:
        return ":wolf: rabid wolf"

    def buildrec(self, **kwargs):
        rec = {}
        rec["name"] = self.name
        rec["roomid"] = self.roomid
        rec["healthpoints"] = self.healthpoints
        return rec

    def on_turn(self, args, room=None, **kwargs) -> bool:
        import random as randomlib

        player = kwargs.get("player", None)
        if player is None:
            io.echo("You do not exist! Go Away!")
            util.logentry(
                "murdermotel.rabidwolf.turn.100: player does not exist",
                logger_name="murdermotel",
            )
            return False

        attacked = kwargs.get("attacked", False)
        ignored = kwargs.get("ignored", False)

        if attacked:
            if util.diceroll(10, mode="single") < WOLF_AUTO_ATTACK_CHANCE:
                damage = randomlib.randint(1, 10) + 10
                io.echo(f"damage={damage}", level="debug")
                io.echo(
                    f"The {self.short()} claws you for {util.pluralize(damage, 'move', 'moves')}"
                )
                player.moves -= damage
                if player.moves < 0:
                    player.moves = 0
                    io.echo("You are out of moves. You are dead.")
                player.save()

        if ignored:
            if util.diceroll(10, mode="single") < WOLF_AUTO_ATTACK_CHANCE:
                io.echo(f"The {self.short()} attacks you!")
                damage = randomlib.randint(1, 10) + 10
                io.echo(f"damage={damage}", level="debug")
                io.echo(
                    f"The {self.short()} claws you for {util.pluralize(damage, 'move', 'moves')}"
                )
                player.moves -= damage
                if player.moves < 0:
                    player.moves = 0
                    io.echo("You are out of moves. You are dead.")
                player.save()

        pool = getattr(self, "pool", None)
        if pool:
            self.save()

        return True

    def save(self, **kwargs) -> bool:
        def _work(conn):
            rec = self.buildrec()
            database.update(
                self.args,
                f"{libmm.SCHEMA}.rabidwolf",
                self.name,
                rec,
                primarykey="name",
                conn=conn,
            )
            return True

        conn = kwargs.get("conn", None) or self.conn
        if conn is None:
            if self.pool is None:
                io.echo(f"mm.RabidWolf.save.100: {self.pool=}", level="error")
                return False
            with database.connect(self.args, pool=self.pool) as conn:
                _work(conn)
        else:
            _work(conn)
        return True


def access(
    args: argparse.Namespace, op: str, obj=None, room=None, **kwargs: Any
) -> bool:
    return True


def init(args: argparse.Namespace, obj=None, room=None, **kwargs: Any) -> bool:
    return True


def buildargs(args, obj=None, room=None, **kwargs):
    return None


def load(args: argparse.Namespace, **kwargs) -> Optional[RabidWolf]:
    def _work(conn):
        with database.cursor(conn) as cur:
            params = {"name": WOLF_NAME}
            q = database.query(
                "SELECT name FROM $murdermotel.npc WHERE name = :name", **params
            )
            cur.execute(q, params)
            npc_exists = cur.rowcount > 0
            if npc_exists:
                io.echo("mm.rabidwolf.load.090: npc record exists", level="debug")

        with database.cursor(conn) as cur:
            params = {"name": WOLF_NAME}
            q = database.query(
                "SELECT * FROM $murdermotel.rabidwolf WHERE name = :name",
                **params,
            )
            cur.execute(q, params)
            if cur.rowcount == 0:
                if npc_exists:
                    io.echo(
                        "mm.rabidwolf.load.100: npc exists but rabidwolf table empty, "
                        "skipping create",
                        level="debug",
                    )
                    return None
                io.echo(
                    "mm.rabidwolf.load.110: no wolf found, can create", level="debug"
                )
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


def create(args: argparse.Namespace, **kwargs) -> RabidWolf | bool:
    pool = kwargs.get("pool", None)
    if pool is None:
        io.echo(f"mm.rabidwolf.create.100: {pool=}", level="error")
        return False

    def _work(conn):
        w = build(
            args,
            {"name": WOLF_NAME, "roomid": 10, "healthpoints": WOLF_HEALTH},
            **kwargs,
        )

        rec = w.buildrec()
        io.echo(f"mm.rabidwolf.create.110: {rec=}", level="debug")

        if not database.upsert(
            args,
            f"{libmm.SCHEMA}.rabidwolf",
            rec,
            conflict_columns=["name"],
            update_columns=["roomid", "healthpoints"],
            mogrify=True,
            conn=conn,
        ):
            io.echo("mm.rabidwolf.create.115: upsert failed", level="error")
            return False

        with database.cursor(conn) as cur:
            params = {
                "name": WOLF_NAME,
                "kind": "rabidwolf",
                "modulepath": "rabidwolf",
                "title": "The Rabid Wolf",
            }
            q = database.query(
                """
                INSERT INTO $murdermotel.npc (name, kind, modulepath, title)
                VALUES (:name, :kind, :modulepath, :title)
                ON CONFLICT (name) DO NOTHING
            """,
                **params,
            )
            cur.execute(q, params)

        with database.cursor(conn) as cur:
            params = {"name": WOLF_NAME}
            q = database.query(
                "SELECT * FROM $murdermotel.rabidwolf WHERE name = :name",
                **params,
            )
            cur.execute(q, params)
            if cur.rowcount > 0:
                rec = cur.fetchone()
                w = build(args, rec, **kwargs)
                return w

        io.echo("mm.rabidwolf.create.120: rabidwolf table corrupted", level="error")
        return False

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


def exists(args: argparse.Namespace, **kwargs: Any) -> bool:
    def _work(conn):
        with database.cursor(conn) as cur:
            q = database.query(
                "SELECT name FROM $murdermotel.rabidwolf WHERE name = :name",
                name=WOLF_NAME,
            )
            cur.execute(q, {"name": WOLF_NAME})
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


def build(args: argparse.Namespace, rec: dict, **kwargs: Any) -> RabidWolf:
    pool = kwargs.get("pool", None)
    w = RabidWolf(args, pool=pool)
    w.name = rec.get("name", WOLF_NAME)
    w.roomid = rec.get("roomid", 10)
    w.healthpoints = rec.get("healthpoints", WOLF_HEALTH)
    return w


def wolf_attack_player(
    args: argparse.Namespace, player: Any, wolf: RabidWolf, **kwargs: Any
) -> None:
    damage = randomlib.randint(1, 10) + 10
    io.echo(f"damage={damage}", level="debug")
    io.echo(
        f"The {wolf.short()} claws you for {util.pluralize(damage, 'move', 'moves')}"
    )
    player.moves -= damage
    if player.moves < 0:
        player.moves = 0
        io.echo("You are out of moves. You are dead.")

    player.save()


def turn(args: argparse.Namespace, **kwargs: Any) -> bool:
    obj = kwargs.get("obj")
    player = kwargs.get("player", None)
    if player is None:
        io.echo("You do not exist! Go Away!")
        util.logentry(
            "murdermotel.rabidwolf.turn.100: player does not exist",
            logger_name="murdermotel",
        )
        return False

    if obj is None:
        io.echo("The wolf does not exist!")
        util.logentry(
            "murdermotel.rabidwolf.turn.120: wolf does not exist",
            logger_name="murdermotel",
        )
        return False

    attacked = kwargs.get("attacked", False)
    ignored = kwargs.get("ignored", False)

    if attacked:
        if util.diceroll(10, mode="single") < WOLF_AUTO_ATTACK_CHANCE:
            wolf_attack_player(args, player, obj, **kwargs)

    if ignored:
        if util.diceroll(10, mode="single") < WOLF_AUTO_ATTACK_CHANCE:
            io.echo(f"The {obj.short()} attacks you!")
            wolf_attack_player(args, player, obj, **kwargs)

    pool = kwargs.get("pool", None)
    if pool:
        obj.save()

    return True


def help(**kwargs: Any) -> Optional[bool]:
    player = kwargs["player"] if "player" in kwargs else None

    if player is None:
        io.echo("You do not exist! Go Away!", level="error")
        return False

    if len(player.weapons()) > 0:
        io.echo("{f6}{var:optioncolor}[A]{var:labelcolor}ttack")
    io.echo(
        "{var:optioncolor}[I]{var:labelcolor}gnore{f6}{var:optioncolor}[F]{var:labelcolor}lee room{f6}"
    )
    return


def attack(
    args: argparse.Namespace,
    player: Any,
    weapons: list[str],
    wolf: RabidWolf,
    **kwargs: Any,
) -> None:
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
        ch = io.inputchoice(
            f"{{var:promptcolor}}kill with? {' '.join(buf)} {{var:inputcolor}}",
            options,
            "",
            **kwargs,
        )
        if ch is None:
            return
        weapon = weapons[ord(ch) - ord("1")]
        io.echo(f"{ch} {{var:sepcolor}}- {{var:labelcolor}}{weapon}")

    io.echo(f"{wolf=}", level="debug")
    damage = util.diceroll(6, mode="single") * 5
    io.echo(f"You remove {damage}% of the {wolf.short()}'s strength!")
    player.moves += 5
    wolf.healthpoints -= damage
    if wolf.healthpoints < 0:
        wolf.healthpoints = 0
    if wolf.healthpoints < 1:
        wolf.roomid = 0
        io.echo(f"You killed the {wolf.short()}!")
        player.moves += 500
        util.logentry(
            f"{player.name} killed the {wolf.short()}!", logger_name="murdermotel"
        )

    if player.moves < 1:
        io.echo("You have died.")
        player.save()
        return

    player.save()

    pool = kwargs.get("pool", None)
    if pool:
        wolf.save()


def flee(args: argparse.Namespace, player: Any, exits: dict) -> None:
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


def main(args: argparse.Namespace, **kwargs: Any) -> bool:
    player = kwargs["player"] if "player" in kwargs else None
    if player is None:
        io.echo("You do not exist! Go Away!")
        return False
    wolf = kwargs["wolf"] if "wolf" in kwargs else None
    if wolf is None:
        io.echo("The wolf does not exist!")
        return False

    room = kwargs["room"] if "room" in kwargs else None
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
        ch = io.inputchoice(
            f"{{var:promptcolor}}Make selection {{var:optioncolor}}[{options}]{{var:promptcolor}}: {{var:inputcolor}}",
            options,
            "",
            help=help,
            player=player,
            **kwargs,
        )
        if ch == "A":
            io.echo(f"Attack {wolf.short()}")
            attack(args, player, weapons, wolf, **kwargs)
            if wolf.roomid == 0:
                break
            wolf.on_turn(args, room=room, attacked=True, **kwargs)
            if player.moves < 1:
                break
        elif ch == "I":
            io.echo("Ignore")
            wolf.on_turn(args, room=room, ignored=True, **kwargs)
            break
        elif ch == "F":
            io.echo("Flee")
            flee(args, player, room.exits)
            break
    return True
