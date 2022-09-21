from random import randint

import ttyio5 as ttyio
import bbsengine5 as bbsengine

from . import lib
from . import data

def init(args, **kw):
    return True

def access(args, op, **kw):
    return True

def main(args, **kw):
    name = bbsengine.getcurrentmembername(args)
    if lib.getroomcount(args) == 0:
        ttyio.echo("{f6}the playground is not set up properly.{f6}")
        return False
    player = lib.Player(args)
    if player.load(name) is False:
        player.roomid = randint(10, lib.getroomcount(args)-10+1)
        player.save()

    bbsengine.title("play")

    loop = True
    while loop:
        if player.moves < 1:
            ttyio.echo("You are out of moves for this call.")
            player.moves = 0
            if ttyio.inputboolean("reset moves? [Yn]: ", "Y") is True:
                player.moves = lib.MOVESPERTURN
                player.turn -= 1
                player.save()

        lib.setarea(args, player, "play")
        room = lib.getroom(args, player.roomid)
        ttyio.echo("room.exits=%r" % (room.exits), level="debug")
        if room is None:
            ttyio.echo("your room does not exist! go away!", level="error")
            return False
#        ttyio.echo("player=%r" % (player), level="debug")

        ttyio.echo("You are %s" % (room.title.title()))
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

        buf = "%s: %s" % (bbsengine.pluralize(len(exitdir), "exit", "exits", quantity=False), bbsengine.oxfordcomma(exitdir, "{lightgray}", "{green}"))
        ttyio.echo(buf)
        ch = ttyio.inputchar("{var:promptcolor}playground: [%s]: {var:inputcolor}" % (options), options+"ZG", "Q")
        if ch == "Q":
            if ttyio.inputboolean(":door: Quit - {var:promptcolor}are you sure? [yN]: {var:inputcolor}", "N") is True:
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
            bbsengine.filedisplay(args, data.get("s.map.floor%d.txt" % (floor)))
        elif ch == "G":
            dest = ttyio.inputstring("goto - room id or shortname: ", noneok=True)
            if dest.isnumeric() is True:
                dest = int(dest)
                if player.roomid == dest:
                    ttyio.echo("You twitch briefly.")
                    continue
                if dest > 0 and dest <= lib.getroomcount(args):
                    player.roomid = dest
                    continue
            
            sql = "select roomid from murdermotel.playground where shortname=%s"
            dat = (dest,)
            dbh = bbsengine.databaseconnect(args)
            cur = dbh.cursor()
            cur.execute(sql, dat)
            if cur.rowcount == 0:
                ttyio.echo("room not found")
                continue
            rec = cur.fetchone()
            if player.roomid == rec["roomid"]:
                ttyio.echo("You twitch briefly.")
                continue
            player.roomid = rec["roomid"]
        elif ch == "Z":
            ttyio.echo("edit room")
            shortname = ttyio.inputstring("{var:promptcolor}room name: {var:inputcolor}", room.shortname, noneok=True)
            if shortname is None:
                continue
            room.shortname = shortname
            room.save()
        elif ch == "?":
            ttyio.echo("menu")
            bbsengine.filedisplay(args, data.get("s.menu.txt"))
        else:
            ttyio.echo()
            continue

        player.moves -= 1
        player.save()
    player.save()

