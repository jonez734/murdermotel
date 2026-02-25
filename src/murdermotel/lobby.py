from bbsengine6 import io, member, database, util

from . import lib as libmm
from . import data

def init(args=None, **kwargs):
    libmm.init(args)
    return True

def access(args, op, **kwargs):
    return True

def buildargs(args, **kwargs):
    return None

def lobbyhelp(**kwargs):
    # io.echo(f"mm.lobby.lobbyhelp.100: {kwargs=}", level="debug")
    args = kwargs.pop("args", None)

    io.echo("{var:optioncolor}[G]{var:labelcolor}ame instructions")
    io.echo("{var:optioncolor}[C]{var:labelcolor}redits")
    if member.checkflag(args, "sysop", **kwargs) is True:
        io.echo("{var:optioncolor}[M]{var:labelcolor}aintenance")
        io.echo("{var:optioncolor}[H]{var:labelcolor}ousekeeping")
    io.echo("{var:optioncolor}[P]{var:labelcolor}lay")
    io.echo("{f6}{var:optioncolor}[Q]{var:labelcolor}uit")
    
def main(args, **kwargs):
    io.echo(f"{kwargs=}", level="debug")
    name = member.getcurrentmoniker(args, **kwargs)
    if args.debug is True:
        io.echo(f"mm.lobby.100: {name=}", level="debug")

    if libmm.runmodule(args, "startup", **kwargs) is False:
        io.echo("failed to start up", level="error")
        return False

    player = None
    done = False
    while not done:
        libmm.setarea(args, player, "lobby", help=True, **kwargs)

        util.heading("murder motel lobby")
        io.echo(f"database: {args.databasename} host: {args.databasehost}:{args.databaseport}", level="debug")
        io.echo()

        options = "GC"
        if member.checkflag(args, "sysop", **kwargs) is True:
            options += "MH"
            
        options += "P"
        options = "".join(sorted(options, key=str.upper))
        options += "Q"
        
        ch = io.inputchoice(f"{{var:promptcolor}}:hotel: lobby [{options}]: {{var:inputcolor}}", options, "", help=lobbyhelp, args=args, **kwargs)
        if ch == "G":
            io.echo("Game Instructions")
            libmm.setarea(args, player, "reading: 'game instructions'")
            util.filedisplay(data.get("s.explain.txt"), more=False)
        elif ch == "C":
            io.echo("Credits")
            libmm.setarea(args, player, "reading: 'credits'")
            util.filedisplay(data.get("s.credits.txt"), more=False)
        elif ch == "Q":
            io.echo(":door: Quit")
            done = True
            break
        elif ch == "M":
            io.echo("Maintenance")
            res = libmm.runmodule(args, "maintenance", **kwargs)
        elif ch == "H":
            io.echo("Housekeeping")
            res = libmm.runmodule(args, "housekeeping", **kwargs)
        elif ch == "P":
            io.echo("Play!")
            res = libmm.runmodule(args, "play", **kwargs) # bbsengine.module.runsubmodule(args, "murdermotel.play", player=player)
            io.echo(f"end play! {res=}")
        else:
            io.echo("{bell}", end="", flush=True)
