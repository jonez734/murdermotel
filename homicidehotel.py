import time
import locale
import argparse

import ttyio5 as ttyio
import bbsengine5 as bbsengine

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

def setarea(args, player, left):
    def right():
        debug = True if args is not None and args.debug is True else False

        if player is not None:
            if player.isdirty is True:
                isdirty = "*"
            else:
                isdirty = ""
            debug = " | debug" if args is not None and args.debug is True else ""

            turn = " | %s" % (bbsengine.pluralize(4-player.turn, "turn remains", "turns remain"))

            return "homicide hotel | %s%s%s%s" % (isdirty, player.name, turn, debug)
        else:
            if debug is True:
                return "debug"
            else:
                return ""
    bbsengine.setarea(left, right)
    return

def init(args=None):
    return

def buildargs(args=None):
    parser = argparse.ArgumentParser("homicidehotel")
    
    parser.add_argument("--verbose", action="store_true", dest="verbose")
    
    parser.add_argument("--debug", action="store_true", dest="debug")

    defaults = {"databasename": "zoidweb5", "databasehost":"localhost", "databaseuser": None, "databaseport":5432, "databasepassword":None}
    bbsengine.buildargdatabasegroup(parser, defaults)
    return parser
    
def main(args):
    parser = buildargs(args)
    args = parser.parse_args()

    if args is not None and "debug" in args and args.debug is True:
        ttyio.echo("hh.main.100: args=%r" % (args))

    ttyio.echo("{f6:3}{cursorup:3}") #  curpos:%d,0}" % (ttyio.getterminalheight()-5))
    bbsengine.initscreen(bottommargin=1)
    player = Player(args, "test-1", (0,0,0))
    setarea(args, player, "homicide hotel")

    done = False

    while not done:
        bbsengine.title("homicide hotel")
        ttyio.echo("database: %s host: %s:%s" % (args.databasename, args.databasehost, args.databaseport), level="debug")
        options = ""
        ttyio.echo("[E]xplain")
        options += "E"
        ttyio.echo("[C]redits")
        options += "C"
        if bbsengine.checksysop(args) is True:
            ttyio.echo("[S]etup")
            options += "S"
        ttyio.echo("{f6}[Q]uit")
        options += "Q"
        ch = ttyio.inputchar("prompt: ", options, "")
        if ch == "E":
            ttyio.echo("Explain #1")
            buf = ""
            with open("s.explain-1.txt") as explainfile:
                for line in explainfile:
                    line = line.replace("\n", "")
                    buf += line
            ttyio.echo(buf)
        elif ch == "C":
            ttyio.echo("Credits")
#            buf = ""
            with open('s.credits.txt') as creditsfile:
                for line in creditsfile:
#                    line = line.strip()
#                    line = ttyio.interpretmci(line)
                    ttyio.echo(line)
#                    buf += line
#                    ttyio.echo(line, end="")
        elif ch == "Q":
            ttyio.echo(":door: Quit")
            done = True

if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    time.tzset()

    parser = buildargs()
    args = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        ttyio.echo("{/all}{bold}INTR{bold}")
    except EOFError:
        ttyio.echo("{/all}{bold}EOF{/bold}")
    finally:
        ttyio.echo("{decsc}{curpos:%d,0}{el}{decrc}{reset}{/all}" % (ttyio.getterminalheight()))
