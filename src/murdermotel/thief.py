from bbsengine6 import io, util

from . import lib

def init(args, **kw):
    return True

def access(args, op, **kw):
    return True

def main(args, **kw):
    player = kw["player"] if "player" in kw else None
    if player is None:
        io.echo("You do not exist! Go Away!")
        util.logentry("murdermotel.thief.main.100: player does not exist", prg="murdermotel")
        return False
    thief = kw["thief"] if "thief" in kw else None
    if thief is None:
        io.echo("The thief does not exist!")
        util.logentry("murdermotel.thief.main.120: thief does not exist", prg="murdermotel")
        return False
    io.echo("THIEF! THIEF!  You were ATTACKED!")
    player.moves -= 5
    if util.diceroll(10) < 4:
        # pick item at random
        # set 'thiefroomid' (uq) to 0
        pass

    player.save()
    return True
