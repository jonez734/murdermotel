import random

import ttyio5 as ttyio
import bbsengine5 as bbsengine

from . import lib

def init(args, **kw):
    return True

def access(args, op, **kw):
    return True

def main(args, **kw):
    player = kw["player"] if "player" in kw else None
    if player is None:
        ttyio.echo("You do not exist! Go Away!")
        bbsengine.util.logentry("murdermotel.thief.main.100: player does not exist")
        return False
    thief = kw["thief"] if "thief" in kw else None
    if thief is None:
        ttyio.echo("The thief does not exist!")
        bbsengine.util.logentry("murdermotel.thief.main.120: thief does not exist")
        return False
    ttyio.echo("THIEF! THIEF!  You were ATTACKED!")
    player.moves -= 5
    if bbsengine.diceroll(10) < 4:
        # pick item at random
        # set 'thiefroomid' (uq) to 0
        pass

    player.save()
    return True
