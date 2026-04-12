import ttyio5 as ttyio
import bbsengine5 as bbsengine

from . import lib


def init(args=None, **kw):
    ttyio.setvariable("menuoption", "{white}{bggray}")
    ttyio.setvariable("menudesc", "{/bgcolor}{white}")
    ttyio.setvariable("menuvalue", "{/bgcolor}{green}")
    ttyio.setvariable("promptcolor", "{/bgcolor}{lightgray}")
    ttyio.setvariable("inputcolor", "{/bgcolor}{green}")


def main(args, **kw):
    if args is not None and "debug" in args and args.debug is True:
        ttyio.echo("hotelsetup.main.100: args=%r" % (args))

    player = lib.getcurrentplayer()

    done = False
    while not done:
        bbsengine.title("murder motel housekeeping")
        ttyio.echo(
            "database: %s host: %s:%s"
            % (args.databasename, args.databasehost, args.databaseport),
            level="debug",
        )
        lib.setarea(args, player, "housekeeping")
        ttyio.echo("{var:menuoption}[S]{var:menudesc}etup")
        ttyio.echo("{var:menuoption}[E]{var:menudesc}dit")
        ttyio.echo("{f6}{var:menuoption}[Q]{var:menudesc}uit{f6}")
        ch = ttyio.inputchar(
            "{var:promptcolor}housekeeping {var:optioncolor}[SEQ]{var:promptcolor}: {var:inputcolor}",
            "SEQ",
            "",
        )
        if ch == "S":
            ttyio.echo("Setup Game")
            lib.runsubmodule(args, player, "setup")
        if ch == "E":
            ttyio.echo("Edit")
            lib.runsubmodule(args, player, "edit")
        if ch == "Q":
            ttyio.echo("Q - Quit")
            done = True
    return True
