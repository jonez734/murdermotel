import argparse

import bbsengine5 as bbsengine
import ttyio5 as ttyio

from . import lib

def init(args=None):
    return lib.init(args)

def buildargs(args=None):
    parser = argparse.ArgumentParser("murdermotel")
    
    parser.add_argument("--verbose", action="store_true", dest="verbose")
    
    parser.add_argument("--debug", action="store_true", dest="debug")
    
    parser.add_argument("--terminalwidth", action="store", dest="terminalwidth", default=ttyio.getterminalwidth())

    defaults = {"databasename": "zoidweb5", "databasehost":"localhost", "databaseuser": None, "databaseport":5432, "databasepassword":None}
    bbsengine.buildargdatabasegroup(parser, defaults)
    return parser

def access(args):
    return True

def main(args):
    if args is not None and "debug" in args and args.debug is True:
        ttyio.echo("mm.main.100: args=%r" % (args), level="debug")

    ttyio.echo("{f6:3}{cursorup:3}") #  curpos:%d,0}" % (ttyio.getterminalheight()-5))
    bbsengine.initscreen(bottommargin=1)
    player = lib.Player(args, "testplayer-1", (0,0,0))
    lib.setarea(args, player, "murder motel")
    lib.setcurrentplayer(player)

    lib.runsubmodule(args, player, "lobby")
