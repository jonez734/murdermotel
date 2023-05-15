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
        return False
    thief = kw["thief"] if "thief" in kw else None
    if thief is None:
        ttyio.echo("The thief does not exist!")
        return False
    ttyio.echo("THIEF! THIEF!  You were ATTACKED!")
    player.moves -= 5
    player.save()
    return True
