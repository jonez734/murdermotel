import time
import locale
import argparse

from bbsengine6 import io, screen, database

from . import lib as libmm


def init(args, **kwargs: dict) -> bool:
    io.register_emojis({"robot": "\U0001f916"})

    screen.init(args)
    return True


def access(args, op: str, **kwargs: dict) -> bool:
    return True


def buildargs(args=None, **kwargs: dict):
    parser = argparse.ArgumentParser("murder motel")
    return parser


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    time.tzset()

    parser = libmm.buildargs()
    args = parser.parse_args()

    init(args)

    with database.getpool(args) as pool:
        try:
            libmm.runmodule(args, "run", "lobby", pool=pool)
        except KeyboardInterrupt:
            io.echo("{/all}*INTR*")
        except EOFError:
            io.echo("{/all}*EOF*")
        finally:
            io.echo(
                f"{{decsc}}{{curpos:{io.terminal.height()},0}}{{el}}{{reset}}{{decrc}}"
            )
