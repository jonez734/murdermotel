import time
import locale
import argparse
import ttyio5 as ttyio
import bbsengine5 as bbsengine

def init(args=None):
  ttyio.setvariable("menuoption", "{white}{bggray}")
  ttyio.setvariable("menudesc", "{/bgcolor}{white}")
  ttyio.setvariable("menuvalue", "{/bgcolor}{green}")
  ttyio.setvariable("promptcolor", "{/bgcolor}{lightgray}")
  ttyio.setvariable("inputcolor", "{/bgcolor}{green}")

def buildargs(args=None):
    parser = argparse.ArgumentParser("homicidehotel")
    parser.add_argument("--verbose", action="store_true", dest="verbose")
    parser.add_argument("--debug", action="store_true", dest="debug")

    defaults = {"databasename": "zoidweb5", "databasehost":"localhost", "databaseuser": None, "databaseport":15433, "databasepassword":None} # port=5432
    bbsengine.buildargdatabasegroup(parser, defaults)

    return parser

def setarea(args, left, dirty=False):
  def right():
    currentmember = bbsengine.getcurrentmember(args)
    if currentmember is None:
      return ""
    rightbuf = "| %s | %s" % (currentmember["name"], bbsengine.pluralize(currentmember["credits"], "credit", "credits"))
    if args.debug is True:
      rightbuf += " | debug"
    if dirty is True:
      rightbuf += " | dirty"
    return rightbuf
  bbsengine.setarea(left, right)

def main(args):
    if args is not None and "debug" in args and args.debug is True:
        ttyio.echo("hotelsetup.main.100: args=%r" % (args))

    done = False
    while not done:
      bbsengine.title("homicide hotel housekeeping")
      ttyio.echo("database: %s host: %s:%s" % (args.databasename, args.databasehost, args.databaseport), level="debug")
      setarea(args, "homicide hotel housekeeping")
      ttyio.echo("{var:menuoption}[S]{var:menudesc}etup")
      ttyio.echo("{var:menuoption}[E]{var:menudesc}dit")
      ttyio.echo("{f6}{var:menuoption}[Q]{var:menudesc}uit{f6}")
      ch = ttyio.inputchar("{var:promptcolor}housekeeping [SEQ]: {var:inputcolor}", "SEQ", "")
      if ch == "S":
        bbsengine.runsubmodule(args, "hh.setup")
      if ch == "E":
        bbsengine.runsubmodule(args, "hh.edit")
      if ch == "Q":
        ttyio.echo("Q - Quit")
        done = True
    return True

if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    time.tzset()

    parser = buildargs()
    args = parser.parse_args()

    ttyio.echo("{f6:3}{cursorup:3}") # curpos:%d,0}" % (ttyio.getterminalheight()-3))
    bbsengine.initscreen(bottommargin=1)

    init(args)

    try:
        main(args)
    except KeyboardInterrupt:
        ttyio.echo("{/all}{bold}INTR{bold}")
    except EOFError:
        ttyio.echo("{/all}{bold}EOF{/bold}")
    finally:
        ttyio.echo("{decsc}{curpos:%d,0}{el}{decrc}{reset}{/all}" % (ttyio.getterminalheight()))
