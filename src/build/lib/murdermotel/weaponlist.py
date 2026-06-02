import argparse

from bbsengine6 import database, io, member


def init(args: argparse.Namespace | None = None, **kw: dict) -> bool:
    return True


def access(args: argparse.Namespace, op: str, **kw: dict) -> bool | None:
    return member.issysop(args)


def buildargs(args: argparse.Namespace, **kw: dict) -> argparse.ArgumentParser | None:
    return None


def main(args: argparse.Namespace, **kw: dict) -> bool | None:
    pool = kw.get("pool", None)
    if pool is None:
        io.echo(f"mm.weaponlist.main.100: {pool=}", level="error")
        return False

    with database.connect(args, pool=pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                "select item.kind, item.name, item.serial, playground.roomid, playground.title as playgroundtitle, item.title as itemtitle from murdermotel.map_item_room as map, murdermotel.item as item, murdermotel.playground where map.roomid = playground.roomid and map.itemname = item.name and map.serial = item.serial and item.kind = 'component' order by item.name, item.serial asc"
            )
            cur.execute(q)
            for rec in database.resultiter(cur):
                io.echo(
                    f"{rec['name']}-{rec['serial']} ({rec['kind']}) is {rec['playgroundtitle']} (#{rec['roomid']})"
                )
    return True
