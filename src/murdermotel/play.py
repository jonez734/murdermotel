import argparse
import copy
import random
from typing import Any, Optional

from bbsengine6 import io, util, database, member

from . import (
    lib as libmm,
    data,
    player as libplayer,
    room as libroom,
    thief as libthief,
    rabidwolf as libwolf,
    boobytrap as libboobytrap,
)
from .lib import registry


def init(args: argparse.Namespace, **kwargs: Any) -> bool:
    return True


def access(args: argparse.Namespace, op: str, **kwargs: Any) -> bool:
    return True


def buildargs(args: argparse.Namespace, **kwargs: Any) -> Optional[str]:
    return None


def maintmode(args: argparse.Namespace, **kwargs: Any) -> bool:
    player: Any = kwargs.get("player", None)
    if player is None:
        io.echo("You do not exist! Go Away!")
        return False

    room: Any = kwargs.get("room", None)
    if room is None:
        io.echo("Your room does not exist! Go away!")
        return False

    def editroom() -> bool:
        io.echo("edit room")
        shortname: Optional[str] = io.inputstring(
            "{var:promptcolor}room short name: {var:inputcolor}",
            room.shortname,
            noneok=True,
        )
        if shortname is None:
            return True
        room.shortname = shortname
        room.save()
        return True

    def goto() -> bool:
        conn = kwargs.get("conn", None)
        if conn is None:
            pool = kwargs.get("pool", None)
            if pool is None:
                io.echo(f"mm.play.maint.goto.100: {pool=}", level="error")
                return False

        dest: Optional[str] = io.inputstring(
            "{var:promptcolor}goto - room id or shortname: {var:inputcolor}",
            noneok=True,
        )
        if dest is None or dest == "":
            return True

        if dest.isnumeric() is True:
            dest_int: int = int(dest)
            if player.roomid == dest_int:
                io.echo("You twitch briefly.")
                return True
            if dest_int > 0 and dest_int <= libroom.getcount(args, **kwargs):
                player.roomid = dest_int
                return True

        room_obj: Any = libroom.load(args, dest, **kwargs)
        if not room_obj:
            io.echo(
                f"{{var:labelcolor}}room '{{var:valuecolor}}{dest}{{var:labelcolor}}' not found"
            )
            return False

        player.roomid = room_obj.id
        player.moves -= 2
        player.save()

        with database.cursor(conn) as cur:
            sql = "select id from murdermotel.playground where shortname=%s"
            dat = (dest,)
            cur.execute(sql, dat)
            if cur.rowcount == 0:
                io.echo("room not found")
                return False
            rec = cur.fetchone()
            if rec is None:
                io.echo("room not found")
                return False
            if player.roomid == rec["id"]:
                io.echo("You twitch briefly.")
                return True
            player.roomid = rec["id"]

        return True

    io.echo("Z - Maint Mode ", end="")
    ch: Optional[str] = io.inputchoice(
        "{var:optioncolor}[G]{var:labelcolor}oto {var:optioncolor}[E]{var:labelcolor}dit room {var:optioncolor}(Q){var:labelcolor}uit",
        "GEQ",
        "Q",
    )
    if ch == "Q":
        return True
    elif ch == "G":
        return goto()
    elif ch == "E":
        return editroom()

    return True


def playgroundhelp(**kwargs: Any) -> bool:
    io.echo(f"mm.play.300: {kwargs=}", level="debug")
    room: Any = kwargs.get("room", None)
    if room is None:
        io.echo("Your room does not exist! Go Away!")
        return False

    player: Any = kwargs.get("player", None)
    if player is None:
        io.echo("You do not exist! Go Away!")
        return False

    for g in ("#", "I", "K", "L", "T", "R", "P", "H"):
        io.setvar(g, "{gray}")
    for g in ("M", "?", "G", "Q"):
        io.setvar(g, "{green}")

    e = (
        ("up", "U"),
        ("down", "D"),
        ("north", "N"),
        ("south", "S"),
        ("east", "E"),
        ("west", "W"),
    )
    for f in e:
        if f[0] in room.exits and room.exits[f[0]] is not None:
            io.setvar(f[1], "{green}")
        else:
            io.setvar(f[1], "{gray}")
    io.setvar("#", "{gray}")
    io.setvar("I", "{green}")
    if len(player.items) < 5:
        io.setvar("T", "{green}")
    if len(player.items) > 0:
        io.setvar("L", "{green}")
    util.filedisplay(data.get("s.menu.txt"), **kwargs)
    return True


def main(args: argparse.Namespace, **kwargs: Any) -> bool:
    from datetime import datetime
    import dateutil.tz

    if libroom.getcount(args, **kwargs) == 0:
        io.echo("{f6}the playground is not set up properly.{f6}")
        return False

    currentmembermoniker: str = member.getcurrentmoniker(args, **kwargs)
    player: Any = libplayer.load(args, currentmembermoniker, **kwargs)

    if not player:
        playermoniker: str = libplayer.inputmoniker(
            "new player moniker: ",
            currentmembermoniker,
            verify=libplayer.verifyPlayerNameNotFound,  # type: ignore[arg-type]
            multiple=False,  # type: ignore[arg-type]
            args=args,  # type: ignore[arg-type]
            returnseq=False,  # type: ignore[arg-type]
            **kwargs,
        )
        if playermoniker == "":
            io.echo("aborted.")
            return False

        player = libplayer.create(args, playermoniker, **kwargs)
        if player is None:
            io.echo("mm.play.main.100: unable to create player", level="error")
            return False

        room_count: int = libroom.getcount(args, **kwargs)
        player.roomid = random.randint(10, room_count - 10 + 1)
        player.save()

    tzlocal = dateutil.tz.tzlocal()
    player.datelastplayed = datetime.now(tzlocal)

    player.info()
    util.heading("playground")

    registry.clear()

    loaded_boobytrap = libboobytrap.load(args, **kwargs)
    if loaded_boobytrap is None:
        loaded_boobytrap = libboobytrap.create(args, **kwargs)
    libmm.BoobyTrap(args, loaded_boobytrap=loaded_boobytrap, **kwargs)
    loaded_thief = libthief.load(args, **kwargs)
    if loaded_thief is None:
        loaded_thief = libthief.create(args, **kwargs)
    libmm.Thief(args, loaded_thief=loaded_thief, **kwargs)
    loaded_wolf = libwolf.load(args, **kwargs)
    if loaded_wolf is None:
        loaded_wolf = libwolf.create(args, **kwargs)
    libmm.RabidWolf(args, loaded_wolf=loaded_wolf, **kwargs)

    for obj in registry.all():
        health_info = (
            f" health={obj.healthpoints}" if hasattr(obj, "healthpoints") else ""
        )
        io.echo(f"{obj.short()} roomid={obj.roomid}{health_info}")

    done: bool = False
    while not done:
        roomchange: bool = False

        if player.turn >= libmm.TURNSPERDAY:
            io.echo("You are out of turns for today")
            if (
                io.inputboolean(
                    "{var:promptcolor}reset turns? [Yn]: {var:inputcolor}", "Y"
                )
                is True
            ):
                player.turn = 0

        if player.moves < 1:
            io.echo("You are out of moves for this call.")
            player.moves = 0

            if (
                io.inputboolean(
                    "{var:promptcolor}reset moves? {var:optioncolor}[Yn]{var:promptcolor}: {var:inputcolor}",
                    "Y",
                )
                is True
            ):
                player.moves = libmm.DEFAULTMOVESPERTURN
                if player.turn > 0:
                    player.turn += 1

        player.save()

        libmm.setarea(args, player, "playground", help=True, **kwargs)
        room: Any = libroom.load(args, player.roomid, **kwargs)
        if not room:
            io.echo("your room does not exist! go away!", level="error")
            return False
        if args.debug is True:
            io.echo(f"mm.play.220: {room.exits=}", level="debug")

        io.echo(f"{{var:labelcolor}}You are {room.title.title()}")

        if args.debug is True:
            io.echo("mm.play.200: {room.items=}", level="debug")

        if len(room.items) > 0:
            label: str = util.pluralize(
                len(room.items), "item", "items", quantity=False
            )
            value: str = util.oxfordcomma(room.items)
            io.echo(f"{{var:labelcolor}}room {label}: {{var:valuecolor}}{value}")

        if len(player.items) > 0:
            label = util.pluralize(len(player.items), "item", "items", quantity=False)
            items: list = copy.deepcopy(player.items)
            items = player.weapons(items) + items
            value = util.oxfordcomma(items)
            io.echo(f"{{var:labelcolor}}player {label}: {{var:valuecolor}}{value}")

        for obj in registry.get_by_room(player.roomid):
            io.echo(f"{obj.short()}")
            if hasattr(obj, "name") and obj.name == "wolf":
                currentroomid: int = player.roomid
                if (
                    libmm.runsubmodule(args, "rabidwolf", room=room, wolf=obj, **kwargs)
                    is False
                ):
                    io.echo("trouble running 'rabidwolf' prg")
                    return False
                if player.roomid != currentroomid:
                    continue
            obj.on_turn(args, room=room, **kwargs)

        for obj in registry.all():
            if hasattr(obj, "name") and obj.name == "boobytrap":
                obj.on_turn(args, room=room, **kwargs)

        if roomchange is True:
            continue
        options: str = "QM?"
        exitdir: list = []
        for k, v in room.exits.items():
            if v is None:
                continue

            if k == "north":
                options += "N"
            elif k == "south":
                options += "S"
            elif k == "east":
                options += "E"
            elif k == "west":
                options += "W"
            elif k == "up":
                options += "U"
            elif k == "down":
                options += "D"
            exitdir.append(k)

        io.echo(f"len(player.items)={len(player.items)}", level="debug")
        if len(room.items) > 0 and len(player.items) <= libmm.MAXITEMSPERPLAYER:
            options += "T"

        if len(player.items) > 0:
            options += "L"

        options += "I"

        players = libmm.getroomplayers(args, room.id, **kwargs)
        io.echo(
            ":person: {var:labelcolor}%s: {var:valuecolor}%s"
            % (
                util.pluralize(len(players), "player", "players", quantity=False),
                util.oxfordcomma(players),
            )
        )

        io.echo(
            ":door: {var:labelcolor}%s: {var:valuecolor}%s"
            % (
                util.pluralize(len(exitdir), "exit", "exits", quantity=False),
                util.oxfordcomma(exitdir),
            )
        )

        for obj in registry.all():
            io.echo(f"{obj.short()} roomid={obj.roomid}")

        options = "".join(sorted(options))
        ch: Optional[str] = io.inputchar(
            f"{{var:promptcolor}}playground: [{options}]: {{var:inputcolor}}",
            options + "ZG",
            "Q",
            help=playgroundhelp,
            player=player,
            args=args,
            room=room,
        )

        if ch is None:
            continue

        if ch == "Q":
            if (
                io.inputboolean(
                    ":door: Quit - {var:promptcolor}are you sure? {var:optioncolor}[yN]{var:promptcolor}: {var:inputcolor}",
                    "N",
                )
                is True
            ):
                done = True
                continue
        elif ch == "N":
            io.echo("north")
            player.roomid = room.exits["north"]
        elif ch == "S":
            io.echo("south")
            player.roomid = room.exits["south"]
        elif ch == "E":
            io.echo("east")
            player.roomid = room.exits["east"]
        elif ch == "W":
            io.echo("west")
            player.roomid = room.exits["west"]
        elif ch == "U":
            io.echo("up")
            player.roomid = room.exits["up"]
        elif ch == "D":
            io.echo("down")
            player.roomid = room.exits["down"]
        elif ch == "M":
            floor: int = io.inputinteger(
                "map - {var:promptcolor}floor (1-5): {var:inputcolor}"
            )
            if floor < 1 or floor > 5:
                io.echo("invalid floor")
                continue
            util.filedisplay(data.get(f"s.map.floor{floor}.txt"), wordwrap=False)
        elif ch == "G":
            util.filedisplay(data.get("s.explain.txt"))
        elif ch == "Z":
            res = maintmode(args, player=player, room=room, **kwargs)
            if res is False:
                io.echo("something went wrong.")
                continue
        elif ch == "?" or ch == "KEY_HELP" or ch == "KEY_F1":
            io.echo("menu")
            util.filedisplay(data.get("s.menu.txt"))
        elif ch == "T":
            itemname: Optional[str] = io.inputstring(
                "Take - {var:promptcolor}item name: {var:inputcolor}",
                noneok=True,
                completer=libmm.completeItemName(args, roomid=player.roomid),
            )
            if itemname == "":
                io.echo("aborted.")
                continue
            itemindex: Optional[int] = room.finditem(itemname)
            if itemindex is None:
                io.echo(f"The {itemname!r} is not here.", level="error")
                return False

            item = room.items[itemindex]
            del room.items[itemindex]
            player.items.append(item)
            player.save()
            room.save()
        elif ch == "L":
            itemname = io.inputstring(
                "Leave - {var:promptcolor}item name: {var:inputcolor}",
                noneok=True,
                completer=libmm.completeItemName(args, playername=player.moniker),
            )
            itemindex = player.finditem(itemname)
            if itemindex is None:
                io.echo("aborted.", level="error")
                continue
            io.echo(f"mm.play.118: {player.items=} {itemindex=}", level="debug")
            item = player.items[itemindex]
            del player.items[itemindex]
            io.echo(f"mm.play.120: {item=}", level="debug")
            room.items.append(item)

            player.save()
            room.save()
        elif ch == "I":
            io.echo("Info")
            player.info()

        io.echo()
        player.moves -= 1
        player.save()
        room.save()
        for obj in registry.all():
            if hasattr(obj, "name"):
                if obj.name == "thief":
                    obj.save(**kwargs)
                elif obj.name == "wolf":
                    obj.save(**kwargs)
                elif obj.name == "boobytrap":
                    obj.save(**kwargs)

        player.on_turn(args, room=room, **kwargs)

    return True
