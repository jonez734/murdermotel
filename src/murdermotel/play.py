import argparse
import copy
import random
from typing import Any, Optional

from bbsengine6 import io, util, member, module as bbsmodule

from . import (
    lib as libmm,
    data,
    player as libplayer,
    room as libroom,
    thief as libthief,
    rabidwolf as libwolf,
    boobytrap as libboobytrap,
    bot as libbot,
)


def init(args: argparse.Namespace, **kwargs: Any) -> bool:
    return True


def access(args: argparse.Namespace, op: str, **kwargs: Any) -> bool:
    return True


def buildargs(args: argparse.Namespace, **kwargs: Any) -> Optional[str]:
    return None


def _handle_trap(args, room, player, direction, **kwargs):
    """Handle trap room movement. Returns new room ID or None if no escape."""
    from . import traproom as libtraproom

    io.echo(
        f"play._handle_trap: direction={direction} roomid={room.id} modulepath={room.modulepath}"
    )

    trap_exits = getattr(room, "TRAP_EXITS", None)
    if trap_exits is not None and direction not in trap_exits:
        io.echo(
            f"play._handle_trap: direction {direction} not in TRAP_EXITS, using normal exit"
        )
        return None

    module = room.modulepath
    if not module:
        io.echo("play._handle_trap: no modulepath")
        return None

    io.echo(f"play._handle_trap: calling on_turn() for {module}")
    result = room.on_turn(args, room=room, player=player, **kwargs)
    io.echo(f"play._handle_trap: on_turn returned {result}")

    if result is False:
        trap_msg = getattr(room, "TRAP_MESSAGE", libtraproom.TRAP_MESSAGE)
        io.echo(f"play._handle_trap: {trap_msg}")
        return None

    for op in ("success", "solved", "win"):
        io.echo(f"play._handle_trap: trying op={op}")
        new_room = libmm.runmodule(
            args,
            op,
            module,
            obj=room,
            room=room,
            player=player,
            **kwargs,
        )
        io.echo(f"play._handle_trap: {op} returned {new_room}")
        if new_room:
            io.echo(f"play._handle_trap: escaping to room {new_room}")
            return new_room

    io.echo("play._handle_trap: no escape found, staying")
    return player.roomid


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
            **kwargs,
        )
        if shortname is None:
            return True
        room.shortname = shortname
        room.save()
        return True

    def goto() -> bool:
        conn = kwargs.get("conn", None)
        pool = kwargs.get("pool", None)
        if conn is None and pool is None:
            io.echo(f"mm.play.maint.goto.100: {pool=}", level="error")
            return False

        dest: Optional[str] = io.inputstring(
            "{var:promptcolor}goto - room id or shortname: {var:inputcolor}",
            noneok=True,
            **kwargs,
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

        return True

    io.echo("Z - Maint Mode ", end="")
    ch: Optional[str] = io.inputchoice(
        "{var:optioncolor}[G]{var:labelcolor}oto {var:optioncolor}[E]{var:labelcolor}dit room {var:optioncolor}[R]{var:labelcolor}eload {var:optioncolor}(Q){var:labelcolor}uit",
        "GERQ",
        "Q",
        **kwargs,
    )
    if ch == "Q":
        return True
    elif ch == "G":
        return goto()
    elif ch == "R":
        return reload(args, player=player, **kwargs)
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

    currentmembermoniker: str = member.getcurrentmoniker(args, **kwargs) or ""
    io.echo("starting call to libplayer.load", level="debug")
    player: Any = libplayer.load(args, currentmembermoniker, **kwargs)
    io.echo("ended call", level="debug")

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

    io.echo("starting call to libbot.get_alive_bots", level="debug")
    bots = libbot.get_alive_bots(args, **kwargs)
    io.echo("ended call", level="debug")
    player_monikers = [currentmembermoniker]
    if not player.target:
        libbot.assign_targets(args, player_monikers, bots, **kwargs)

    tzlocal = dateutil.tz.tzlocal()
    player.datelastplayed = datetime.now(tzlocal)
    player.module = "player"

    io.echo("starting call to player.info()", level="debug")
    player.info()
    io.echo("ending call to player.info()", level="debug")

    if player.target:
        io.echo(f"{{var:labelcolor}}You are hunting: {{var:valuecolor}}{player.target}")

    util.heading("playground")

    libmm.registry.clear()
    libmm.registry.register(player)

    loaded_boobytrap = libboobytrap.load(args, **kwargs)
    if loaded_boobytrap is None:
        loaded_boobytrap = libboobytrap.create(args, **kwargs)
    if libmm.registry.get_by_name("boobytrap") is None:
        libboobytrap.BoobyTrap(args, loaded_boobytrap=loaded_boobytrap, **kwargs)
    loaded_thief = libthief.load(args, **kwargs)
    if loaded_thief is None:
        loaded_thief = libthief.create(args, **kwargs)
    if libmm.registry.get_by_name("thief") is None:
        libthief.Thief(args, loaded_thief=loaded_thief, **kwargs)
    loaded_wolf = libwolf.load(args, **kwargs)
    if loaded_wolf is None:
        loaded_wolf = libwolf.create(args, **kwargs)
    if libmm.registry.get_by_name("rabidwolf") is None:
        libwolf.RabidWolf(args, loaded_wolf=loaded_wolf, **kwargs)

    ##    from . import bot as libbot

    bots = libbot.get_alive_bots(args, **kwargs)
    for b in bots:
        if libmm.registry.get_by_name(b.name) is None:
            libmm.registry.register(b)

    for obj in libmm.registry.all():
        if hasattr(obj, "module") and obj.module:
            modulename = f"murdermotel.{obj.module}"
            if bbsmodule.check(args, modulename, op="init") is False:
                io.echo(f"check failed for {obj.module}", level="error")
                continue
            bbsmodule.run(args, modulename, obj=obj, room=None, **kwargs)

    for obj in libmm.registry.all():
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
                    "{var:promptcolor}reset turns? [Yn]: {var:inputcolor}",
                    "Y",
                    **kwargs,
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
                    **kwargs,
                )
                is True
            ):
                player.moves = libmm.DEFAULTMOVESPERTURN
                if player.turn > 0:
                    player.turn += 1

        io.echo("playloop.100: about to save player", level="debug")
        player.save()
        io.echo("playloop.120: ended player save", level="debug")
        conn = kwargs.get("conn", None)
        pool = kwargs.get("pool", None)
        if conn is None and pool is None:
            io.echo(f"mm.play.playloop.100: {pool=}", level="error")
            return False
        libmm.setarea(args, player, "playground", help=True, **kwargs)
        room: Any = libroom.load(args, player.roomid, **kwargs)
        if not room:
            io.echo("your room does not exist! go away!", level="error")
            return False

        room.on_turn(args, room=room, player=player, **kwargs)
        if args.debug is True:
            io.echo(f"mm.play.220: {room.exits=}", level="debug")

        io.echo(f"{{var:labelcolor}}You are {room.title.title()}")

        if args.debug is True:
            io.echo("mm.play.200: {room.items=}", level="debug")

        if len(room.items) > 0:
            label: str = util.pluralize(
                len(room.items), "item", "items", quantity=False
            )
            value: str = util.oxfordcomma(room.items) or ""
            io.echo(f"{{var:labelcolor}}room {label}: {{var:valuecolor}}{value}")

        if len(player.items) > 0:
            label = util.pluralize(len(player.items), "item", "items", quantity=False)
            items: list = copy.deepcopy(player.items)
            items = player.weapons(items) + items
            value = util.oxfordcomma(items) or ""
            io.echo(f"{{var:labelcolor}}player {label}: {{var:valuecolor}}{value}")

        for obj in libmm.registry.get_by_room(player.roomid):
            io.echo(f"{obj.short()}")
            obj.on_turn(args, room=room, player=player, **kwargs)

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

        ##        from . import bot as libbot

        bots_in_room = [
            b
            for b in libbot.get_alive_bots(args, pool=kwargs.get("pool"))
            if b.roomid == room.id
        ]
        if bots_in_room:
            io.echo(
                ":robot: {var:labelcolor}%s: {var:valuecolor}%s"
                % (
                    util.pluralize(len(bots_in_room), "bot", "bots", quantity=False),
                    util.oxfordcomma([b.short() for b in bots_in_room]),
                )
            )

        io.echo(
            ":door: {var:labelcolor}%s: {var:valuecolor}%s"
            % (
                util.pluralize(len(exitdir), "exit", "exits", quantity=False),
                util.oxfordcomma(exitdir),
            )
        )

        options = "".join(sorted(options))
        ch: Optional[str] = io.inputchoice(
            f"{{var:promptcolor}}playground: [{options}]: {{var:inputcolor}}",
            options + "ZG",
            "Q",
            help=playgroundhelp,
            player=player,
            args=args,
            room=room,
            **kwargs,
        )

        if ch is None:
            continue

        if ch == "Q":
            if (
                io.inputboolean(
                    ":door: Quit - {var:promptcolor}are you sure? {var:optioncolor}[yN]{var:promptcolor}: {var:inputcolor}",
                    "N",
                    **kwargs,
                )
                is True
            ):
                done = True
                continue
        elif ch == "N":
            new_room = _handle_trap(args, room, player, "N", **kwargs)
            if new_room is not None:
                player.roomid = new_room
            else:
                player.roomid = room.exits["north"]
        elif ch == "S":
            new_room = _handle_trap(args, room, player, "S", **kwargs)
            if new_room is not None:
                player.roomid = new_room
            else:
                player.roomid = room.exits["south"]
        elif ch == "E":
            new_room = _handle_trap(args, room, player, "E", **kwargs)
            if new_room is not None:
                player.roomid = new_room
            else:
                player.roomid = room.exits["east"]
        elif ch == "W":
            new_room = _handle_trap(args, room, player, "W", **kwargs)
            if new_room is not None:
                player.roomid = new_room
            else:
                player.roomid = room.exits["west"]
        elif ch == "U":
            new_room = _handle_trap(args, room, player, "U", **kwargs)
            if new_room is not None:
                player.roomid = new_room
            else:
                player.roomid = room.exits["up"]
        elif ch == "D":
            new_room = _handle_trap(args, room, player, "D", **kwargs)
            if new_room is not None:
                player.roomid = new_room
            else:
                player.roomid = room.exits["down"]
        elif ch == "M":
            floor_input = io.inputinteger(
                "map - {var:promptcolor}floor (1-5): {var:inputcolor}", **kwargs
            )
            floor: int = floor_input if isinstance(floor_input, int) else 1
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
                **kwargs,
            )
            if itemname == "":
                io.echo("aborted.")
                continue
            itemindex: Optional[int] = room.finditem(itemname)
            if itemindex is None:
                io.echo(f"The {itemname!r} is not here.", level="error")
                continue

            item = room.items[itemindex]
            del room.items[itemindex]
            player.items.append(item)
            conn = kwargs.get("conn", None)
            pool = kwargs.get("pool", None)
            if conn is None and pool is not None:
                conn = pool.getconn()
                player.save(conn=conn)
                room.save(conn=conn)
                conn.commit()
                pool.putconn(conn)
            else:
                player.save(conn=conn) if conn else player.save()
                room.save(conn=conn) if conn else room.save()
        elif ch == "L":
            itemname = io.inputstring(
                "Leave - {var:promptcolor}item name: {var:inputcolor}",
                noneok=True,
                completer=libmm.completeItemName(args, playername=player.moniker),
                **kwargs,
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

            conn = kwargs.get("conn", None)
            pool = kwargs.get("pool", None)
            if conn is None and pool is not None:
                conn = pool.getconn()
                player.save(conn=conn)
                room.save(conn=conn)
                conn.commit()
                pool.putconn(conn)
            else:
                player.save(conn=conn) if conn else player.save()
                room.save(conn=conn) if conn else room.save()
        elif ch == "I":
            io.echo("Info")
            player.info()

        io.echo()
        player.moves -= 1
        player.save()
        room.save()
        for obj in libmm.registry.all():
            if hasattr(obj, "name"):
                if obj.name == "thief":
                    obj.save(**kwargs)
                elif obj.name == "wolf":
                    obj.save(**kwargs)
                elif obj.name == "boobytrap":
                    obj.save(**kwargs)

        player.on_turn(args, room=room, **kwargs)

    io.echo("exiting play loop", level="debug")
    return True


def reload(args: argparse.Namespace, player: Any, **kwargs: Any) -> bool:
    if not member.checkflag(args, "SYSOP"):
        io.echo("Sysop access required.", level="error")
        return False

    io.echo("Reload: ", end="")
    ch: Optional[str] = io.inputchoice(
        "{var:optioncolor}[T]{var:labelcolor}his object  {var:optioncolor}[P]{var:labelcolor}ath (all same type)  {var:optioncolor}[M]{var:labelcolor}odule (enter name)  {var:optioncolor}[A]{var:labelcolor}ll objects",
        "TPMA",
        "Q",
        **kwargs,
    )

    if ch == "Q" or ch is None:
        return True

    if ch == "T":
        count = 1
        libmm.reload_module(player)
        io.echo("Reloaded module for this object.")
    elif ch == "P":
        modulepath = getattr(player, "modulepath", None)
        if modulepath is None:
            io.echo("This object has no modulepath.", level="warn")
            return False
        count = libmm.reload_modulepath(modulepath)
        io.echo(f"Reloaded {count} object(s) with modulepath={modulepath!r}.")
    elif ch == "M":
        modulepath: Optional[str] = io.inputstring(
            "{var:promptcolor}modulepath: {var:inputcolor}",
            noneok=True,
            **kwargs,
        )
        if modulepath is None or modulepath == "":
            return True
        count = libmm.reload_modulepath(modulepath)
        io.echo(f"Reloaded {count} object(s) with modulepath={modulepath!r}.")
    elif ch == "A":
        count = libmm.reload_all_modules()
        io.echo(f"Reloaded {count} object(s) total.")

    return True
