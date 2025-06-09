import time
import locale
import argparse

from bbsengine6 import io, screen

from . import lib, version

def init(args, **kw:dict) -> bool:
    screen.init(args)
    return True

def access(args, op:str, **kw:dict) -> bool:
    return True

def buildargs(args=None, **kw:dict):
    parser = argparse.ArgumentParser("murder motel")
    return parser

if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    time.tzset()

    parser = lib.buildargs()
    args = parser.parse_args()

    init(args)

    try:
        lib.runmodule(args, "lobby")
    except KeyboardInterrupt:
        io.echo("{/all}{bold}INTR{bold}")
    except EOFError:
        io.echo("{/all}{bold}EOF{/bold}")
    finally:
        io.echo("{decsc}{curpos:%d,0}{el}{decrc}{reset}{/all}" % (io.getterminalheight()))
