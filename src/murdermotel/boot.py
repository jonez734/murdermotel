import argparse

import bbsengine6 as bbsengine
import ttyio6 as ttyio

from . import lib

def init(args=None, **kw):
    return lib.init(args)

def buildargs(args=None, **kw):
    parser = argparse.ArgumentParser("murdermotel")
    
    parser.add_argument("--verbose", action="store_true", dest="verbose")
    
    parser.add_argument("--debug", action="store_true", dest="debug")
    
    parser.add_argument("--terminalwidth", action="store", dest="terminalwidth", default=ttyio.getterminalwidth())
    
    parser.add_argument("--node", action="store", dest="node", default="cyclops")

    defaults = {"databasename": "zoid6", "databasehost":"localhost", "databaseuser": None, "databaseport":5432, "databasepassword":None}
    bbsengine.database.buildargdatabasegroup(parser, defaults)
    return parser

def access(args, op, **kw) -> bool:
    return True

def main(args, **kw):
    if args is not None and "debug" in args and args.debug is True:
        ttyio.echo("mm.main.100: args=%r" % (args), level="debug")

    ttyio.echo("{f6:3}{cursorup:3}") #  curpos:%d,0}" % (ttyio.getterminalheight()-5))
    bbsengine.screen.init()
    player = None
    lib.setarea(args, player, "murder motel")
    lib.runsubmodule(args, player, "lobby")
    return True
