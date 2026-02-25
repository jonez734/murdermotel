from bbsengine6 import io, util

from . import lib

def init(args, **kwargs):
    return True

def save(args):
    return True

def turn(args, **kwargs):
    player = kwargs.get("player", None)
    if player is None:
        io.echo("You do not exist! Go Away!")
        util.logentry("murdermotel.thief.main.100: player does not exist", prg="murdermotel")
        return False
    thief = kwargs.get("thief", None)
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
