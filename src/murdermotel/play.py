import copy
import random

from bbsengine6 import io, util, database, member

from . import lib as libmm, data, player as libplayer, room as libroom

def init(args, **kwargs):
    return True

def access(args, op, **kwargs):
    return True

def buildargs(args, **kwargs):
    return None

def maintmode(args, **kwargs):
    def editroom():
        io.echo("edit room")
        shortname = io.inputstring("{var:promptcolor}room short name: {var:inputcolor}", room.shortname, noneok=True)
        if shortname is None:
            return True
        room.shortname = shortname
        room.save()
    def goto():
        conn = kwargs.get("conn", None)
        if conn is None:
            pool = kwargs.get("pool", None)
            if pool is None:
                io.echo(f"mm.play.maint.goto.100: {pool=}", level="error")
                return False

        dest = io.inputstring("{var:promptcolor}goto - room id or shortname: {var:inputcolor}", noneok=True)
        if dest.isnumeric() is True:
            dest = int(dest)
            if player.roomid == dest:
                io.echo("You twitch briefly.")
                return True
            if dest > 0 and dest <= libroom.getcount(args, **kwargs):
                player.roomid = dest
                return True
        room = libroom.load(args, dest, **kwargs)
        if room is None:
            io.echo(f"{{var:labelcolor}}room '{{var:valuecolor}}{dest}{{var:labelcolor}}' not found")
            return False
        
        player.roomid = room.id
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
            if player.roomid == rec["id"]:
                io.echo("You twitch briefly.")
                return True
            player.roomid = rec["id"]
    
    player = kwargs.get("player", None)
    if player is None:
        io.echo("You do not exist! Go Away!")
        return False
    
    room = kwargs.get("room", None)
    if room is None:
        io.echo("Your room does not exist! Go away!")
        return False

    io.echo("Z - Maint Mode ", end="")
    ch = io.inputchoice(f"{{var:optioncolor}}[G]{{var:labelcolor}}oto {{var:optioncolor}}[E]{{var:labelcolor}}dit room {{var:optioncolor}}(Q){{var:labelcolor}}uit", "GEQ", "Q")
    if ch == "Q":
        return True
    elif ch == "G":
        goto()
    elif ch == "E":
        editroom()
    
    return True

def playgroundhelp(**kwargs):
    io.echo(f"mm.play.300: {kwargs=}", level="debug")
    room = kwargs["room"] if "room" in kwargs else None
    if room is None:
        io.echo("Your room does not exist! Go Away!")
        return False

    player = kwargs["player"] if "player" in kwargs else None
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

def main(args, **kwargs):
    from datetime import datetime
    import dateutil.tz

    if libroom.getcount(args, **kwargs) == 0:
        io.echo("{f6}the playground is not set up properly.{f6}")
        return False
    currentmembermoniker = member.getcurrentmoniker(args, **kwargs)
    player = libplayer.load(args, currentmembermoniker, **kwargs)
    if player is None:
        playermoniker = libplayer.inputmoniker("new player moniker: ", currentmembermoniker, verify=libplayer.verifyPlayerNameNotFound, multiple=False, args=args, returnseq=False, **kwargs)
        if playermoniker == "":
            io.echo("aborted.")
            return False

        player = libplayer.create(args, playermoniker, **kwargs)
        if player is None:
            io.echo(f"mm.play.main.100: unable to create player", level="error")
            return False
        player.roomid = random.randint(10, libroom.getcount(args, **kwargs)-10+1)
        player.save()

    tzlocal = dateutil.tz.tzlocal()
    player.datelastplayed = datetime.now(tzlocal)

    player.info()
    util.heading("playground")

    boobytrap = libmm.BoobyTrap(args, **kwargs)
    thief = libmm.Thief(args, **kwargs)
    wolf = libmm.RabidWolf(args, **kwargs)

    io.echo(f"{wolf.short()}  roomid={wolf.roomid} health={wolf.healthpoints}")
    io.echo(f"{thief.short()} roomid={thief.roomid}") # supervillian
    io.echo(f"{boobytrap.short()} roomid={boobytrap.roomid}")

    done = False
    while not done:
        roomchange = False

        if player.turn >= libmm.TURNSPERDAY:
            io.echo("You are out of turns for today")
            if io.inputboolean("{var:promptcolor}reset turns? [Yn]: {var:inputcolor}", "Y") is True:
                player.turn = 0

        if player.moves < 1:
            io.echo("You are out of moves for this call.")
            player.moves = 0

            if io.inputboolean("{var:promptcolor}reset moves? {var:optioncolor}[Yn]{var:promptcolor}: {var:inputcolor}", "Y") is True:
                player.moves = libmm.MOVESPERTURN
                if player.turn > 0:
                    player.turn += 1

        player.save()

        libmm.setarea(args, player, "playground", help=True, **kwargs)
        room = libroom.load(args, player.roomid, **kwargs)
        if room is None:
            io.echo("your room does not exist! go away!", level="error")
            return False
        if args.debug is True:
            io.echo(f"mm.play.220: {room.exits=}", level="debug")
#        ttyio.echo("player=%r" % (player), level="debug")

        io.echo(f"{{var:labelcolor}}You are {room.title.title()}")

        if args.debug is True:
            io.echo("mm.play.200: {room.items=}", level="debug")

        if len(room.items) > 0:
            label = util.pluralize(len(room.items), "item", "items", quantity=False)
            value = util.oxfordcomma(room.items)
            io.echo(f"{{var:labelcolor}}room {label}: {{var:valuecolor}}{value}")

        if len(player.items) > 0:
            label = util.pluralize(len(player.items), "item", "items", quantity=False)
            items = copy.deepcopy(player.items)
            items = player.weapons(items)+items
            value = util.oxfordcomma(items)
            io.echo(f"{{var:labelcolor}}player {label}: {{var:valuecolor}}{value}")

        if player.roomid == wolf.roomid:
            currentroomid = player.roomid
            if libmm.runmodule(args, "rabidwolf", room=room, wolf=wolf, **kwargs) is False:
                io.echo("trouble running 'rabidwolf' prg")
                return False
            if player.roomid != currentroomid:
                continue

        if player.roomid == thief.roomid:
            io.echo("{var:highlightcolor}the :supervillian: thief{var:labelcolor} is here. watch your back!")
        
        if player.roomid == boobytrap.roomid:
            io.echo(f"{boobytrap.short()}")

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
        io.echo(f"len(player.items)={len(player.items)}", level="debug")
        if len(room.items) > 0 and len(player.items) <= libmm.MAXITEMSPERPLAYER:
            options += "T"
        
        if len(player.items) > 0:
            options += "L"
        
        options += "I"
        
        players = libmm.getroomplayers(args, room.id, **kwargs)
        io.echo(":person: {var:labelcolor}%s: {var:valuecolor}%s" % (util.pluralize(len(players), "player", "players", quantity=False), util.oxfordcomma(players)))
        
        io.echo(":door: {var:labelcolor}%s: {var:valuecolor}%s" % (util.pluralize(len(exitdir), "exit", "exits", quantity=False), util.oxfordcomma(exitdir)))
        
        io.echo(f"{wolf.short()} roomid={wolf.roomid}")
        
#        pi = player.getitems()
#        if len(pi) == 0:
#            ttyio.echo("{var:labelcolor}you have {var:valuecolor}no items")
#        else:
#            ttyio.echo(f"{{var:labelcolor}}you have {{var:valuecolor}}{bbsengine.util.pluralize(len(pi), 'item', 'items')}: {bbsengine.util.oxfordcomma(pi)}")
        
        options = "".join(sorted(options))
        ch = io.inputchar(f"{{var:promptcolor}}playground: [{options}]: {{var:inputcolor}}", options+"ZG", "Q", help=playgroundhelp, player=player, args=args, room=room)
        if ch == "Q":
            if io.inputboolean(":door: Quit - {var:promptcolor}are you sure? {var:optioncolor}[yN]{var:promptcolor}: {var:inputcolor}", "N") is True:
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
            floor = io.inputinteger("map - {var:promptcolor}floor (1-5): {var:inputcolor}")
            if floor < 1 or floor > 5:
                # if an invalid floor is entered, do not deduct a move
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
#        elif ch == "Z":
#            io.echo("edit room")
#            shortname = io.inputstring("{var:promptcolor}room short name: {var:inputcolor}", room.shortname, noneok=True)
#            if shortname is None:
#                continue
#            room.shortname = shortname
#            room.save()
        elif ch == "?" or ch == "KEY_HELP":
            io.echo("menu")
            util.filedisplay(data.get("s.menu.txt"))
        elif ch == "T":
            itemname = io.inputstring("Take - {var:promptcolor}item name: {var:inputcolor}", noneok=True, completer=libmm.completeItemName(args, roomid=player.roomid))
            if itemname == "":
                io.echo("aborted.")
                continue
            itemindex = room.finditem(itemname)
            if itemindex is None:
                io.echo(f"The {itemname!r} is not here.", level="error")
                return

            item = room.items[itemindex]
            del room.items[itemindex]
            player.items.append(item)
            player.save()
            room.save()
        elif ch == "L":
            itemname = io.inputstring("Leave - {var:promptcolor}item name: {var:inputcolor}", noneok=True, completer=libmm.completeItemName(args, playername=player.name))
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
