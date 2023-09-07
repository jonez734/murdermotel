import ttyio6 as ttyio
import bbsengine6 as bbsengine

from . import lib
from . import data

def init(args=None, **kw):
    lib.init(args)
    return True

def lobbyhelp(**kw):
    args = kw["args"] if "args" in kw else None

    ttyio.echo("{var:optioncolor}[G]{var:labelcolor}ame instructions")
    ttyio.echo("{var:optioncolor}[C]{var:labelcolor}redits")
    if bbsengine.member.checkflag(args, "SYSOP") is True:
        ttyio.echo("{var:optioncolor}[M]{var:labelcolor}aintenance")
        ttyio.echo("{var:optioncolor}[H]{var:labelcolor}ousekeeping")
    ttyio.echo("{var:optioncolor}[P]{var:labelcolor}lay")
    ttyio.echo("{f6}{var:optioncolor}[Q]{var:labelcolor}uit")
    
def main(args, **kw):
    name = bbsengine.member.getcurrentmoniker(args)
    if args.debug is True:
        ttyio.echo("mm.lobby.100: name=%r" % (name), level="debug")

    player = None
    done = False
    while not done:
        lib.setarea(args, player, "lobby", help=True)

        bbsengine.util.heading("murder motel lobby")
        ttyio.echo("database: %s host: %s:%s" % (args.databasename, args.databasehost, args.databaseport), level="debug")
        ttyio.echo()

        ttyio.echo(f"check={bbsengine.database.classexists(args, 'murdermotel.playground')!r}")
        if bbsengine.database.classexists(args, "murdermotel") is True:
            if bbsengine.member.checkflag(args, "SYSOP") == True:
                ttyio.echo("SysOP, please use 'maint mode' to create playground.")
            ttyio.echo("murdermotel schema does not exist. ")
        else:
            ttyio.echo("murdermotel schema exists")

        options = ""
        options += "G"
        options += "C"
        if bbsengine.member.checkflag(args, "SYSOP") is True:
            options += "MH"
            
        options += "P"
        options = "".join(sorted(options, key=str.upper))
        options += "Q"
        
        ch = ttyio.inputchoice(f"{{var:promptcolor}}:hotel: lobby [{options}]: {{var:inputcolor}}", options, "", help=lobbyhelp, args=args)
        if ch == "G":
            ttyio.echo("Game Instructions")
            lib.setarea(args, player, "reading: 'game instructions'")
            bbsengine.util.filedisplay(data.get("s.explain.txt"), more=False)
        elif ch == "C":
            ttyio.echo("Credits")
            lib.setarea(args, player, "reading: 'credits'")
            bbsengine.util.filedisplay(data.get("s.credits.txt"), more=False)
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
            ttyio.echo("Play!")
            res = lib.runsubmodule(args, player, "play") # bbsengine.module.runsubmodule(args, "murdermotel.play", player=player)
            ttyio.echo(f"end play! res={res!r}")
        else:
            ttyio.echo("{bell}", end="", flush=True)
