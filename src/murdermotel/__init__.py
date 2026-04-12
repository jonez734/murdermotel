from bbsengine6 import util
from . import lib


def init(args, **kw: dict) -> bool:
    return True


def access(args, op: str, **kw: dict) -> bool:
    return True


def buildargs(args, **kw: dict) -> bool:
    return None


def main(args, **kw: dict):
    util.heading("murder motel")
    lib.runmodule(args, "lobby")
    return True
