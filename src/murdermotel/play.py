import copy
import random

import ttyio6 as ttyio
import bbsengine6 as bbsengine

from . import lib
from . import data

def init(args, **kw):
    return True

def access(args, op, **kw):
    return True

def maintmode(args, **kw):
    def editroom():
        ttyio.echo("edit room")
        shortname = ttyio.inputstring("{var:promptcolor}room short name: {var:inputcolor}", room.shortname, noneok=True)
        if shortname is None:
            return True
        room.shortname = shortname
        room.save()
    def goto():
        dest = ttyio.inputstring("{var:promptcolor}goto - room id or shortname: {var:inputcolor}", noneok=True)
        if dest.isnumeric() is True:
            dest = int(dest)
            if player.roomid == dest:
                ttyio.echo("You twitch briefly.")
                return True
            if dest > 0 and dest <= lib.getroomcount(args):
                player.roomid = dest
                return True
        
        sql = "select roomid from murdermotel.playground where shortname=%s"
        dat = (dest,)
        dbh = bbsengine.database.connect(args)
        cur = dbh.cursor()
        cur.execute(sql, dat)
        if cur.rowcount == 0:
            ttyio.echo("room not found")
            return False
        rec = cur.fetchone()
        if player.roomid == rec["roomid"]:
            ttyio.echo("You twitch briefly.")
            return True
        player.roomid = rec["roomid"]
    
    player = kw["player"] if "player" in kw else None
    if player is None:
        ttyio.echo("You do not exist! Go Away!")
        return False
    
    room = kw["room"] if "room" in kw else None
    if room is None:
        ttyio.echo("Your room does not exist! Go away!")
        return False

    ttyio.echo("Z - Maint Mode")
    ch = ttyio.inputchar("[G]oto [E]dit room [Q]uit", "GEQ", "Q")
    if ch == "Q":
        return True
    elif ch == "G":
        goto()
    elif ch == "E":
        editroom()
    
    return True

def playgroundhelp(**kw):
    ttyio.echo(f"kw={kw!r}")
    room = kw["room"] if "room" in kw else None
    if room is None:
        ttyio.echo("Your room does not exist! Go Away!")
        return False

    player = kw["player"] if "player" in kw else None
    if player is None:
        ttyio.echo("You do not exist! Go Away!")
        return False
    
    for g in ("#", "I", "K", "L", "T", "R", "P", "H"):
        ttyio.setvar(g, "{gray}")
    for g in ("M", "?", "G", "Q"):
        ttyio.setvar(g, "{green}")
    
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
            ttyio.setvar(f[1], "{green}")
        else:
            ttyio.setvar(f[1], "{gray}")
    ttyio.setvar("#", "{gray}")
    ttyio.setvar("I", "{green}")
    if len(player.items) < 5:
        ttyio.setvar("T", "{green}")
    if len(player.items) > 0:
        ttyio.setvar("L", "{green}")
    bbsengine.util.filedisplay(data.get("s.menu.txt"), **kw)

def main(args, **kw):
    ttyio.echo("murdermotel.play.100: running!", level="debug")
    name = bbsengine.member.getcurrentmoniker(args)
    if lib.getroomcount(args) == 0:
        ttyio.echo("{f6}the playground is not set up properly.{f6}")
        return False
    player = lib.Player(args)
    if player.load(name) is False:
        player.roomid = random.randint(10, lib.getroomcount(args)-10+1)
        player.save()

    bbsengine.screen.heading("playground")

    boobytrap = lib.BoobyTrap(args)
    thief = lib.Thief(args)
    wolf = lib.RabidWolf(args)
    ttyio.echo(f"{wolf.short()} roomid={wolf.roomid} health={wolf.healthpoints}")
    ttyio.echo(f":supervillian: thief roomid={thief.roomid}")

    loop = True
    while loop:
        roomchange = False

        if player.turn >= lib.TURNSPERDAY:
            ttyio.echo("You are out of turns for today")
            if ttyio.inputboolean("{var:promptcolor}reset turns? [Yn]: {var:inputcolor}", "Y") is True:
                player.turn = 0

        if player.moves < 1:
            ttyio.echo("You are out of moves for this call.")
            player.moves = 0

            if ttyio.inputboolean("{var:promptcolor}reset moves? {var:optioncolor}[Yn]{var:promptcolor}: {var:inputcolor}", "Y") is True:
                player.moves = lib.MOVESPERTURN
                if player.turn > 0:
                    player.turn += 1

        player.save()

        lib.setarea(args, player, "playground", help=True)
        room = lib.getroom(args, player.roomid)
        if room is None:
            ttyio.echo("your room does not exist! go away!", level="error")
            return False
        if args.debug is True:
            ttyio.echo(f"room.exits={room.exits!r}", level="debug")
#        ttyio.echo("player=%r" % (player), level="debug")

        ttyio.echo(f"{{var:labelcolor}}You are {room.title.title()}")

        if args.debug is True:
            ttyio.echo("roomitems={room.items!r}", level="debug")

        if len(room.items) > 0:
            label = bbsengine.util.pluralize(len(room.items), "item", "items", quantity=False)
            value = bbsengine.util.oxfordcomma(room.items)
            ttyio.echo(f"{{var:labelcolor}}room {label}: {{var:valuecolor}}{value}")

        if len(player.items) > 0:
            label = bbsengine.util.pluralize(len(player.items), "item", "items", quantity=False)
            items = copy.deepcopy(player.items)
            items = player.weapons(items)+items
            value = bbsengine.util.oxfordcomma(items)
            ttyio.echo(f"{{var:labelcolor}}player {label}: {{var:valuecolor}}{value}")

        if wolf.roomid == player.roomid:
            if lib.runsubmodule(args, player, "rabidwolf", room=room, wolf=wolf) is False:
                ttyio.echo("Trouble running 'rabidwolf' prg")
                return False

        if player.roomid == thief.roomid:
            ttyio.echo("{var:highlightcolor}the :supervillian: thief{var:labelcolor} is here. watch your back!")
        
        if roomchange is True:
            continue
        options = "QM?"
        exitdir = []
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

#        ttyio.echo(f"roomitems={len(room.items)} playeritems={len(player.items)}", level="debug")
        # limit to 2 defenses
        ttyio.echo(f"len(player.items)={len(player.items)}", level="debug")
        if len(room.items) > 0 and len(player.items) <= lib.MAXITEMSPERPLAYER:
            options += "T"
        
        if len(player.items) > 0:
            options += "L"
        
        options += "I"
        
        players = lib.getroomplayers(args, room.roomid)
        ttyio.echo(":person: {var:labelcolor}%s: {var:valuecolor}%s" % (bbsengine.util.pluralize(len(players), "player", "players", quantity=False), bbsengine.util.oxfordcomma(players)))
        
        ttyio.echo(":door: {var:labelcolor}%s: {var:valuecolor}%s" % (bbsengine.util.pluralize(len(exitdir), "exit", "exits", quantity=False), bbsengine.util.oxfordcomma(exitdir)))
        
        ttyio.echo(f"{wolf.short()} roomid={wolf.roomid}")
        
        ttyio.echo(f"your items: {bbsengine.util.oxfordcomma(player.getitems())}")
        
        options = "".join(sorted(options))
        ch = ttyio.inputchar(f"{{var:promptcolor}}playground: [{options}]: {{var:inputcolor}}", options+"ZG", "Q", help=playgroundhelp, player=player, args=args, room=room)
        if ch == "Q":
            if ttyio.inputboolean(":door: Quit - {var:promptcolor}are you sure? {var:optioncolor}[yN]{var:promptcolor}: {var:inputcolor}", "N") is True:
                loop = False
                continue
        elif ch == "N":
            ttyio.echo("north")
            player.roomid = room.exits["north"]
        elif ch == "S":
            ttyio.echo("south")
            player.roomid = room.exits["south"]
        elif ch == "E":
            ttyio.echo("east")
            player.roomid = room.exits["east"]
        elif ch == "W":
            ttyio.echo("west")
            player.roomid = room.exits["west"]
        elif ch == "U":
            ttyio.echo("up")
            player.roomid = room.exits["up"]
        elif ch == "D":
            ttyio.echo("down")
            player.roomid = room.exits["down"]
        elif ch == "M":
            floor = ttyio.inputinteger("map - {var:promptcolor}floor (1-5): {var:inputcolor}")
            if floor < 1 or floor > 5:
                # if an invalid floor is entered, do not deduct a move
                ttyio.echo("invalid floor")
                continue
            bbsengine.util.filedisplay(data.get(f"s.map.floor{floor}.txt"))
        elif ch == "G":
            bbsengine.util.filedisplay(data.get("s.explain.txt"))
        elif ch == "Z":
            res = maintmode(args, player=player, room=room)
            if res is False:
                ttyio.echo("something went wrong.")
                continue
        elif ch == "Z":
            ttyio.echo("edit room")
            shortname = ttyio.inputstring("{var:promptcolor}room short name: {var:inputcolor}", room.shortname, noneok=True)
            if shortname is None:
                continue
            room.shortname = shortname
            room.save()
        elif ch == "?" or ch == "KEY_HELP":
            ttyio.echo("menu")
            bbsengine.util.filedisplay(data.get("s.menu.txt"))
        elif ch == "T":
            itemname = ttyio.inputstring("Take - {var:promptcolor}item name: {var:inputcolor}", noneok=True, completer=lib.completeItemName(args, roomid=player.roomid))
            if itemname == "":
                ttyio.echo("aborted.")
                continue
            itemindex = room.finditem(itemname)
            if itemindex is None:
                ttyio.echo(f"The {itemname} does not exist in this room.", level="error")
                return

            item = room.items[itemindex]
            del room.items[itemindex]
            player.items.append(item)
            player.save()
            room.save()
        elif ch == "L":
            itemname = ttyio.inputstring("Leave - {var:promptcolor}item name: {var:inputcolor}", noneok=True, completer=lib.completeItemName(args, playername=player.name))
            itemindex = player.finditem(itemname)
            if itemindex is None:
                ttyio.echo("aborted.", level="error")
                continue
            ttyio.echo(f"player.items={player.items!r} itemindex={itemindex}", level="debug")
            item = player.items[itemindex]
            del player.items[itemindex]
            ttyio.echo(f"item={item!r}", level="debug")
            room.items.append(item)
            
            player.save()
            room.save()
        elif ch == "I":
            ttyio.echo("Info")
            player.info()
        else:
            ttyio.echo()
            continue

        player.moves -= 1
        player.save()
