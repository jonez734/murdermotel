from bbsengine6 import io


def init(args, obj=None, room=None, **kwargs) -> bool:
    return True


def access(args, op, **kwargs) -> bool:
    return op in ("init", "run")


def buildargs(args, obj=None, room=None, **kwargs):
    return None


def main(args):
    io.echo("pass")
