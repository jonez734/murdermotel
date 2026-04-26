# traproom.py
# Generic trap room framework - inheritance-based

import random

from bbsengine6 import io

from . import room as libroom

ATTEMPTS_ALLOWED = 5
TRAP_MESSAGE = "You are trapped! Try again..."
TRAP_EXITS = None
ESCAPE_MIN = 10
ESCAPE_MAX = None

_counter = {}  # {moniker: turn_count}


class TrapRoom(libroom.Room):
    """Generic trap room - inherit from this class and override config."""

    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self.attempts_allowed = ATTEMPTS_ALLOWED
        self.trap_message = TRAP_MESSAGE
        self.trap_exits = TRAP_EXITS
        self.escape_min = ESCAPE_MIN
        self.escape_max = ESCAPE_MAX

    def on_turn(self, args, room=None, **kwargs):
        """Run attempt logic. Returns True when player can escape."""
        return self.attempt(args, room=room, **kwargs)

    def attempt(self, args, **kwargs) -> bool:
        """Returns True when attempts >= attempts_allowed."""
        player = kwargs.get("player")
        if not player:
            return True

        moniker = player.moniker

        if moniker not in _counter:
            _counter[moniker] = 1
        else:
            _counter[moniker] += 1

        attempts = _counter[moniker]
        allowed = self.attempts_allowed

        io.echo(f"attempt {attempts}/{allowed}", level="debug")

        if attempts >= allowed:
            return True

        return False

    def success(self, args, **kwargs) -> int:
        """Returns random room ID for escape."""
        from . import room as libroom

        max_room = libroom.getcount(args, **kwargs)
        max_val = self.escape_max if self.escape_max is not None else max_room - 10
        return random.randint(self.escape_min, max_val)

    def solved(self, args, **kwargs) -> int:
        """Alias for success(). Override for custom behavior."""
        return self.success(args, **kwargs)

    def win(self, args, **kwargs) -> int:
        """Alias for success(). Override for custom behavior."""
        return self.success(args, **kwargs)

    def reset(self, moniker: str) -> None:
        """Reset counter for a specific player."""
        if moniker in _counter:
            del _counter[moniker]


def init(args, obj=None, room=None, **kwargs) -> bool:
    return True


def access(args, op, **kwargs) -> bool:
    return op in ("init", "run", "turn", "attempt", "success")


def buildargs(args, obj=None, room=None, **kwargs):
    return None


def main(args, **kwargs) -> bool:
    return True


def turn(args, **kwargs):
    """Run attempt logic - returns True when player can escape."""
    return attempt(args, **kwargs)


def attempt(args, **kwargs) -> bool:
    """Standalone attempt() - uses default config."""
    player = kwargs.get("player")
    if not player:
        io.echo("traproom.attempt: no player, returning True")
        return True

    moniker = player.moniker

    if moniker not in _counter:
        _counter[moniker] = 1
    else:
        _counter[moniker] += 1

    attempts = _counter[moniker]
    allowed = ATTEMPTS_ALLOWED

    io.echo(f"traproom.attempt: {moniker} attempt {attempts}/{allowed}")

    if attempts >= allowed:
        io.echo(f"traproom.attempt: {moniker} CAN ESCAPE!")
        return True

    io.echo(f"traproom.attempt: {moniker} still trapped")
    return False


def success(args, **kwargs) -> int:
    """Standalone success() - uses default config."""
    from . import room as libroom

    max_room = libroom.getcount(args, **kwargs)
    max_val = ESCAPE_MAX if ESCAPE_MAX is not None else max_room - 10
    return random.randint(ESCAPE_MIN, max_val)


def solved(args, **kwargs) -> int:
    """Alias for success()."""
    return success(args, **kwargs)


def win(args, **kwargs) -> int:
    """Alias for success()."""
    return success(args, **kwargs)


def reset(args, moniker: str) -> None:
    """Reset counter for a specific player."""
    if moniker in _counter:
        del _counter[moniker]
