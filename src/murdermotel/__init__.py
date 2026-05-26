from bbsengine6 import database, module


def init(args, **kwargs) -> bool:
    return True


def access(args, op: str, **kwargs) -> bool:
    return True


def buildargs(args, **kwargs) -> None:
    return None


def main(args, **kwargs):
    pool = kwargs.get("pool")
    if pool is None:
        with database.getpool(args) as pool:
            module.run(args, "murdermotel.lobby", pool=pool)
    else:
        module.run(args, "murdermotel.lobby", pool=pool)
