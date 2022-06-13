import argparse
import locale

import ttyio5 as ttyio
import bbsengine5 as bbsengine

def main():
    parser = argparse.ArgumentParser("homicidehotel")
    
    parser.add_argument("--verbose", action="store_true", dest="verbose")
    
    parser.add_argument("--debug", action="store_true", dest="debug")

    defaults = {"databasename": "zoidweb5", "databasehost":"localhost", "databaseuser": None, "databaseport":5432, "databasepassword":None}
    bbsengine.buildargdatabasegroup(parser, defaults)

    args = parser.parse_args()

    locale.setlocale(locale.LC_ALL, "")

    if args is not None and "debug" in args and args.debug is True:
        ttyio.echo("hh.main.100: args=%r" % (args))

    ttyio.echo("{f6:5}{curpos:%d,0}" % (ttyio.getterminalheight()-5))
    bbsengine.initscreen(bottommargin=1)

    bbsengine.title("homicide hotel")
    ttyio.echo("database: %s host: %s:%s" % (args.databasename, args.databasehost, args.databaseport), level="debug")
    ttyio.echo("[E]xplain")
    ttyio.echo("[C]redits")
    ttyio.echo("{f6}[Q]uit")
    ch = ttyio.inputchar("prompt: ", "QCE", "")
    if ch == "E":
        ttyio.echo("Explain #1")
        fp = open("s.m.explain-1")
        content = fp.read()
        content.replace("\r\n", "CR")
        fp.close()
        ttyio.echo(content)
    if ch == "C":
        ttyio.echo("Credits")
        fp = open("s.m.credits")
        content = fp.read()
        fp.close()
        ttyio.echo(content)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        ttyio.echo("{/all}{bold}INTR{bold}")
    except EOFError:
        ttyio.echo("{/all}{bold}EOF{/bold}")
    finally:
        ttyio.echo("{decsc}{curpos:%d,0}{el}{decrc}{reset}{/all}" % (ttyio.getterminalheight()))
