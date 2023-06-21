import time
import locale
import argparse

import ttyio6 as ttyio
import bbsengine6 as bbsengine

from . import lib
from . import version

from .boot import *

if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    time.tzset()

    parser = buildargs()
    args = parser.parse_args()

    init(args)

    print("prior to screen.init()")
    bbsengine.screen.init(args)
    print("after")

    try:
        main(args)
    except KeyboardInterrupt:
        ttyio.echo("{/all}{bold}INTR{bold}")
    except EOFError:
        ttyio.echo("{/all}{bold}EOF{/bold}")
    finally:
        ttyio.echo("{decsc}{curpos:%d,0}{el}{decrc}{reset}{/all}" % (ttyio.getterminalheight()))
