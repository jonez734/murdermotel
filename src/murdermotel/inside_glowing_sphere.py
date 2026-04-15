# inside_glowing_sphere.py
# Room #128 - inside a glowing sphere
# Player must try 5 times then escapes to random room (11-130)

from bbsengine6 import io

TURNS_TO_ESCAPE = 5

_counter = {}  # {moniker: turn_count}


def init(args, obj=None, room=None, **kwargs) -> bool:
    return True


def access(args, op, **kwargs) -> bool:
    return op in ("init", "run", "turn", "escape")


def buildargs(args, obj=None, room=None, **kwargs):
    return None


def main(args, **kwargs) -> bool:
    return True


def turn(args, **kwargs):
    obj = kwargs.get("obj")
##    io.echo(f"murdermotel.inside_glowing....100: called", level="debug")
    player = kwargs.get("player")
    if not player:
        return True

    moniker = player.moniker

    if moniker not in _counter:
        _counter[moniker] = 1
    else:
        _counter[moniker] += 1

    io.echo(f"turn {_counter[moniker]}/{TURNS_TO_ESCAPE}", level="debug")

    if _counter[moniker] >= TURNS_TO_ESCAPE:
        del _counter[moniker]
        return True

    return False


def escape(args, **kwargs):
    """Return random room ID 11-(max-10) for escape."""
    from . import room as libroom
    import random

    max_room = libroom.getcount(args, **kwargs)
    return random.randint(10, max_room - 10)
