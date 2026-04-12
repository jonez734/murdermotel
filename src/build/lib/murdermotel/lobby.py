import ttyio5 as ttyio
import bbsengine5 as bbsengine

from . import lib
from . import data


def init(args=None, **kw):
    #    ttyio.echo("hh.frontdesk.init called", level="debug")
    lib.init(args)
    return True


def lobbyhelp(**kw):
    args = kw["args"] if "args" in kw else None

    ttyio.echo("{var:optioncolor}[G]{var:menudesc}ame instructions")
    ttyio.echo("{var:optioncolor}[C]{var:menudesc}redits")
    if bbsengine.checksysop(args) is True:
        ttyio.echo("{var:optioncolor}[M]{var:labelcolor}aintenance")
        ttyio.echo("{var:optioncolor}[H]{var:labelcolor}ousekeeping")
    ttyio.echo("{var:optioncolor}[P]{var:labelcolor}lay")
    ttyio.echo("{f6}{var:optioncolor}[Q]{var:menudesc}uit")


def main(args, **kw):

    name = bbsengine.getmembername(args)
    if args.debug is True:
        ttyio.echo("mm.lobby.100: name=%r" % (name), level="debug")

    player = None
    done = False
    while not done:
        lib.setarea(args, player, "lobby", help=True)

        bbsengine.title("murder motel lobby")
        ttyio.echo(
            "database: %s host: %s:%s"
            % (args.databasename, args.databasehost, args.databaseport),
            level="debug",
        )
        ttyio.echo()

        options = ""
        options += "G"
        options += "C"
        if bbsengine.checksysop(args) is True:
            options += "MH"

        options += "P"
        options = "".join(sorted(options, key=str.upper))
        options += "Q"

        ch = ttyio.inputchar(
            f"{{var:promptcolor}}:hotel: lobby [{options}]: {{var:inputcolor}}",
            options,
            "",
            help=lobbyhelp,
            args=args,
        )
        if ch == "G":
            ttyio.echo("Game Instructions")
            lib.setarea(args, player, "reading: 'game instructions'")
            bbsengine.filedisplay(
                data.get("s.explain.txt"), more=True, width=80, indent=" " * 30
            )
        elif ch == "C":
            ttyio.echo("Credits")
            lib.setarea(args, player, "reading: 'credits'")
            bbsengine.filedisplay(data.get("s.credits.txt"), more=False)
        elif ch == "Q":
            ttyio.echo(":door: Quit")
            done = True
            break
        elif ch == "M":
            ttyio.echo("Maintenance")
            res = lib.runsubmodule(args, player, "maintenance")
        elif ch == "H":
            ttyio.echo("Housekeeping")
            res = lib.runsubmodule(args, player, "housekeeping")
        elif ch == "P":
            ttyio.echo("Play")
            res = lib.runsubmodule(args, player, "play")
        else:
            ttyio.echo("{bell}", end="", flush=True)
