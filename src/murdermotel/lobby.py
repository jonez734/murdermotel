import ttyio5 as ttyio
import bbsengine5 as bbsengine

from . import lib
from . import data

def init(args=None, **kw):
#    ttyio.echo("hh.frontdesk.init called", level="debug")
    lib.init(args)
    return True

def main(args, **kw):
    bbsengine.title("murder motel lobby")
    ttyio.echo("database: %s host: %s:%s" % (args.databasename, args.databasehost, args.databaseport), level="debug")

    player = lib.getcurrentplayer()
    ttyio.echo("frontdesk.main.player=%r" % (player), level="debug")

    done = False
    while not done:
        height = ttyio.getterminalheight()

        lib.setarea(args, player, "front desk")
        options = ""
        ttyio.echo("{var:optioncolor}[G]{var:menudesc}ame instructions")
        options += "G"
        ttyio.echo("{var:optioncolor}[C]{var:menudesc}redits")
        options += "C"
        if bbsengine.checksysop(args) is True:
            ttyio.echo("{var:optioncolor}[M]{var:menudesc}aintenance")
            options += "M"
        ttyio.echo("{var:optioncolor}[P]{var:menudesc}lay")
        options += "P"
        ttyio.echo("{f6}{var:optioncolor}[Q]{var:menudesc}uit")
        options += "Q?"
        ch = ttyio.inputchar("{var:promptcolor}:hotel: front desk [%s]: {var:inputcolor}" % (options), options, "")
        if ch == "G":
            ttyio.echo("Game Instructions")
            lib.setarea(args, player, "reading: 'game instructions'")
            bbsengine.filedisplay(args, data.get("s.explain.txt"), more=True)
        elif ch == "C":
            ttyio.echo("Credits")
            lib.setarea(args, player, "reading: 'credits'")
            bbsengine.filedisplay(args, data.get("s.credits.txt"), more=False)
        elif ch == "Q":
            ttyio.echo(":door: Quit")
            if ttyio.inputboolean("{var:promptcolor}are you sure? [{var:optioncolor}yN{var:promptcolor}]: {var:inputcolor}", "N") is True:
                done = True
        elif ch == "M":
            ttyio.echo("Maintenance")
            res = lib.runsubmodule(args, player, "maintenance")
        elif ch == "P":
            ttyio.echo("Play")
            res = lib.runsubmodule(args, player, "play")
        elif ch == "?":
            ttyio.echo("menu")
            bbsengine.filedisplay(args, data.get("s.menu.txt"))
        else:
            ttyio.echo()
