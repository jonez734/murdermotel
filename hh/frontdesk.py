import ttyio5 as ttyio
import bbsengine5 as bbsengine

import hh.lib as lib

def init(args=None):
#    ttyio.echo("hh.frontdesk.init called", level="debug")
    lib.init(args)
    return True

def main(args):        
    bbsengine.title("homicide hotel front desk")
    ttyio.echo("database: %s host: %s:%s" % (args.databasename, args.databasehost, args.databaseport), level="debug")

    player = lib.getcurrentplayer()
    ttyio.echo("frontdesk.main.player=%r" % (player), level="debug")

    done = False
    while not done:
        lib.setarea(args, player, "front desk")
        options = ""
        ttyio.echo("{var:optioncolor}[G]{var:menudesc}ame instructions")
        options += "G"
        ttyio.echo("{var:optioncolor}[C]{var:menudesc}redits")
        options += "C"
        if bbsengine.checksysop(args) is True:
            ttyio.echo("{var:optioncolor}[H]{var:menudesc}ousekeeping")
            options += "H"
        ttyio.echo("{f6}{var:optioncolor}[Q]{var:menudesc}uit")
        options += "Q?"
        ch = ttyio.inputchar("{var:promptcolor}:hotel: front desk [%s]: {var:inputcolor}" % (options), options, "")
        if ch == "G":
            ttyio.echo("Game Instructions")
            bbsengine.filedisplay(args, "s.explain-1.txt", more=True)
            if ttyio.inputboolean("{var:promptcolor}continue? [{var:optioncolor}Yn{var:promptcolor}]: {var:inputcolor}", "Yn") is True:
                bbsengine.filedisplay(args, "s.explain-2.txt")
        elif ch == "C":
            ttyio.echo("Credits")
            bbsengine.filedisplay(args, "s.credits.txt", more=False)
        elif ch == "Q":
            ttyio.echo(":door: Quit")
            if ttyio.inputboolean("{var:promptcolor}are you sure? [{var:optioncolor}yN{var:promptcolor}]: {var:inputcolor}", "N") is True:
                done = True
        elif ch == "H":
            ttyio.echo("Housekeeping")
            res = bbsengine.runsubmodule(args, "hh.housekeeping")
            if res is None:
                ttyio.echo("!! error running submodule", level="error")
        elif ch == "?":
            ttyio.echo("menu")
            bbsengine.filedisplay(args, "s.menu.txt")
        else:
            ttyio.echo()
