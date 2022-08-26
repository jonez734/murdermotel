import time
import locale
import argparse

import ttyio5 as ttyio
import bbsengine5 as bbsengine

from . import lib
from . import version

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

def main(args):
    if args is not None and "debug" in args and args.debug is True:
        ttyio.echo("mm.main.100: args=%r" % (args), level="debug")

    ttyio.echo("{f6:3}{cursorup:3}") #  curpos:%d,0}" % (ttyio.getterminalheight()-5))
    bbsengine.initscreen(bottommargin=1)
    player = lib.Player(args, "testplayer-1", (0,0,0))
    lib.setarea(args, player, "murder motel")
    lib.setcurrentplayer(player)

    lib.runsubmodule(args, player, "lobby")

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
