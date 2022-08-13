import time
import locale
import argparse

import ttyio5 as ttyio
import bbsengine5 as bbsengine

import hh.lib

class WeaponComponent(object):
    def __init__(self, args, name, location, description):
        self.args = args
        self.name = name
        self.description = description
        self.location = location

class Safety(object):
    def __init__(self, args, name, location, description):
        self.args = args
        self.name = name
        self.location = location
        self.description = description

class Room(object):
    def __init__(self, args, name, location, description):
        self.args = args
        self.name = name
        self.location = location
        self.description = description
        self.contents = []
        self.exits = {}

class Player(object):
    def __init__(self, args, name, location):
        self.args = args
        self.name = name
        self.location = location
        self.isdirty = False
        self.turn = 3

def init(args=None):
    hh.lib.init(args)
    return

def buildargs(args=None):
    parser = argparse.ArgumentParser("homicidehotel")
    
    parser.add_argument("--verbose", action="store_true", dest="verbose")
    
    parser.add_argument("--debug", action="store_true", dest="debug")
    
    parser.add_argument("--terminalwidth", action="store", dest="terminalwidth", default=ttyio.getterminalwidth())

    defaults = {"databasename": "zoidweb5", "databasehost":"localhost", "databaseuser": None, "databaseport":5432, "databasepassword":None}
    bbsengine.buildargdatabasegroup(parser, defaults)
    return parser

def main(args):
    if args is not None and "debug" in args and args.debug is True:
        ttyio.echo("hh.main.100: args=%r" % (args), level="debug")

    ttyio.echo("{f6:3}{cursorup:3}") #  curpos:%d,0}" % (ttyio.getterminalheight()-5))
    bbsengine.initscreen(bottommargin=1)
    player = Player(args, "testplayer-1", (0,0,0))
    hh.lib.setarea(args, player, "homicide hotel")
    hh.lib.setcurrentplayer(player)

    bbsengine.runsubmodule(args, "hh.lobby")
#    bbsengine.runcallback(args, "hh.lobby.init")
#    bbsengine.runcallback(args, "hh.lobby.main")

if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    time.tzset()

    parser = buildargs()
    args = parser.parse_args()

    init(args)

    try:
        main(args)
    except KeyboardInterrupt:
        ttyio.echo("{/all}{bold}INTR{bold}")
    except EOFError:
        ttyio.echo("{/all}{bold}EOF{/bold}")
    finally:
        ttyio.echo("{decsc}{curpos:%d,0}{el}{decrc}{reset}{/all}" % (ttyio.getterminalheight()))
