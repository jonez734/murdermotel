from bbsengine6 import io, member, database, util

from . import lib
from . import data

def init(args=None, **kw):
    lib.init(args)
    return True

def access(args, op, **kw):
    return True

def buildargs(args, **kw):
    return None

def lobbyhelp(**kw):
    args = kw["args"] if "args" in kw else None

    io.echo("{var:optioncolor}[G]{var:labelcolor}ame instructions")
    io.echo("{var:optioncolor}[C]{var:labelcolor}redits")
    if member.checkflag(args, "SYSOP") is True:
        io.echo("{var:optioncolor}[M]{var:labelcolor}aintenance")
        io.echo("{var:optioncolor}[H]{var:labelcolor}ousekeeping")
    io.echo("{var:optioncolor}[P]{var:labelcolor}lay")
    io.echo("{f6}{var:optioncolor}[Q]{var:labelcolor}uit")
    
def main(args, **kw):
    name = member.getcurrentmoniker(args)
    if args.debug is True:
        io.echo("mm.lobby.100: name=%r" % (name), level="debug")

    player = None
    done = False
    while not done:
        lib.setarea(args, player, "lobby", help=True)

        util.heading("murder motel lobby")
        io.echo("database: %s host: %s:%s" % (args.databasename, args.databasehost, args.databaseport), level="debug")
        io.echo()

        io.echo(f"{database.classexists(args, 'murdermotel.playground')=}")
        if database.classexists(args, "murdermotel") is True:
            if member.checkflag(args, "SYSOP") == True:
                io.echo("SysOP, please use 'maint mode' to create playground.")
            io.echo("murdermotel schema does not exist. ")
        else:
            io.echo("murdermotel schema exists")

        options = ""
        options += "G"
        options += "C"
        if member.checkflag(args, "SYSOP") is True:
            options += "MH"
            
        options += "P"
        options = "".join(sorted(options, key=str.upper))
        options += "Q"
        
        ch = io.inputchoice(f"{{var:promptcolor}}:hotel: lobby [{options}]: {{var:inputcolor}}", options, "", help=lobbyhelp, args=args)
        if ch == "G":
            io.echo("Game Instructions")
            lib.setarea(args, player, "reading: 'game instructions'")
            util.filedisplay(data.get("s.explain.txt"), more=False)
        elif ch == "C":
            io.echo("Credits")
            lib.setarea(args, player, "reading: 'credits'")
            util.filedisplay(data.get("s.credits.txt"), more=False)
        elif ch == "Q":
            io.echo(":door: Quit")
            done = True
            break
        elif ch == "M":
            io.echo("Maintenance")
            res = lib.runmodule(args, "maintenance", **kw)
        elif ch == "H":
            io.echo("Housekeeping")
            res = lib.runmodule(args, "housekeeping", **kw)
        elif ch == "P":
            io.echo("Play!")
            res = lib.runmodule(args, "play", **kw) # bbsengine.module.runsubmodule(args, "murdermotel.play", player=player)
            io.echo(f"end play! {res=}")
        else:
            io.echo("{bell}", end="", flush=True)
