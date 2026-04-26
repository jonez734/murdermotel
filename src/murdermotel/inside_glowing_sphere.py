# inside_glowing_sphere.py
# Room #128 - inside a glowing sphere
# Player must try 5 times then escapes to random room (11-max)

from . import traproom as libtraproom


class GlowingSphereTrap(libtraproom.TrapRoom):
    """Trap room inside a glowing sphere."""

    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self.attempts_allowed = 5
        self.trap_message = "You are trapped in the glowing sphere! Try again..."


TRAP_EXITS = None

init = libtraproom.init
access = libtraproom.access
buildargs = libtraproom.buildargs
main = libtraproom.main
turn = libtraproom.turn
attempt = libtraproom.attempt
success = libtraproom.success
solved = libtraproom.solved
win = libtraproom.win
reset = libtraproom.reset
