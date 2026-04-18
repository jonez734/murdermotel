import argparse

from bbsengine6 import io, util, member

from . import lib


def init(args: argparse.Namespace | None = None, **kw: dict) -> bool:
    return True


def access(args: argparse.Namespace, op: str, **kw: dict) -> bool | None:
    return member.checkflag(args, "SYSOP")


def buildargs(args: argparse.Namespace, **kw: dict) -> argparse.ArgumentParser | None:
    return None


def main(args: argparse.Namespace, **kw: dict) -> bool | None:
    if args is not None and "debug" in args and args.debug is True:
        io.echo("hotelsetup.main.100: args=%r" % (args))

    player = kw.get("player", None)

    done = False
    while not done:
        util.heading("murder motel housekeeping")
        io.echo(
            "database: %s host: %s:%s"
            % (args.databasename, args.databasehost, args.databaseport),
            level="debug",
        )
        io.echo()
        lib.setarea(args, player, "housekeeping")
        io.echo("{var:optioncolor}[S]{var:labelcolor}etup")
        io.echo("{var:optioncolor}[E]{var:labelcolor}dit")
        io.echo("{var:optioncolor}[W]{var:labelcolor}eapon list")
        io.echo("{f6}{var:optioncolor}[Q]{var:labelcolor}uit{f6}")
        ch = io.inputchar(
            "{var:promptcolor}housekeeping {var:optioncolor}[SEQW]{var:promptcolor}: {var:inputcolor}",
            "SEQW",
            "",
        )
        if ch == "S":
            io.echo("Setup Game")
            lib.runsubmodule(args, player, "setup")
        elif ch == "E":
            io.echo("Edit")
            lib.runsubmodule(args, player, "edit")
        elif ch == "W":
            io.echo("Weapon list")
            lib.runsubmodule(args, player, "weaponlist")
        elif ch == "Q":
            io.echo("Q - Quit")
            done = True
    return True
