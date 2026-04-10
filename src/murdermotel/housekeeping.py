from bbsengine6 import bbsengine, ttyio, util

from . import lib


def init(args=None, **kw):
    return True


def access(args, op, **kw):
    return bbsengine.checksysop(args)


def main(args, **kw):
    if args is not None and "debug" in args and args.debug is True:
        ttyio.echo("hotelsetup.main.100: args=%r" % (args))

    player = lib.getcurrentplayer()

    done = False
    while not done:
        util.heading("murder motel housekeeping")
        ttyio.echo(
            "database: %s host: %s:%s"
            % (args.databasename, args.databasehost, args.databaseport),
            level="debug",
        )
        ttyio.echo()
        lib.setarea(args, player, "housekeeping")
        ttyio.echo("{var:optioncolor}[S]{var:labelcolor}etup")
        ttyio.echo("{var:optioncolor}[E]{var:labelcolor}dit")
        ttyio.echo("{var:optioncolor}[W]{var:labelcolor}eapon list")
        ttyio.echo("{f6}{var:optioncolor}[Q]{var:labelcolor}uit{f6}")
        ch = ttyio.inputchar(
            "{var:promptcolor}housekeeping {var:optioncolor}[SEQW]{var:promptcolor}: {var:inputcolor}",
            "SEQW",
            "",
        )
        if ch == "S":
            ttyio.echo("Setup Game")
            lib.runsubmodule(args, player, "setup")
        elif ch == "E":
            ttyio.echo("Edit")
            lib.runsubmodule(args, player, "edit")
        elif ch == "W":
            ttyio.echo("Weapon list")
            lib.runsubmodule(args, player, "weaponlist")
        elif ch == "Q":
            ttyio.echo("Q - Quit")
            done = True
    return True
