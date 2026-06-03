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

    from bbsengine6 import util

    done = False
    while not done:
        util.heading("weapon list")
        io.echo("{var:optioncolor}[C]{var:labelcolor}omponents")
        io.echo("{var:optioncolor}[W]{var:labelcolor}eapon recipes")
        io.echo("{f6}{var:optioncolor}[Q]{var:labelcolor}uit{f6}")
        ch = io.inputchar(
            "{var:promptcolor}weapon list {var:optioncolor}[CWQ]{var:promptcolor}: {var:inputcolor}",
            "CWQ",
            "",
        )
        if ch == "C":
            _list_components(args, pool)
        elif ch == "W":
            _list_recipes(args, pool)
        elif ch == "Q":
            done = True
    return True


def _list_components(args: argparse.Namespace, pool) -> bool | None:
    with database.connect(args, pool=pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                """
                SELECT
                    item.kind,
                    item.name,
                    item.serial,
                    map.roomid,
                    playground.title AS playgroundtitle
                FROM murdermotel.map_item_room AS map
                JOIN murdermotel.item ON map.itemname = item.name AND map.serial = item.serial
                JOIN murdermotel.playground ON map.roomid = playground.id
                WHERE item.kind = 'component'
                ORDER BY item.name, item.serial ASC
                """
            )
            cur.execute(q)
            for rec in database.resultiter(cur):
                io.echo(
                    f"{rec['name']}-{rec['serial']} ({rec['kind']}) is {rec['playgroundtitle']} (#{rec['roomid']})"
                )
    return True


def _list_recipes(args: argparse.Namespace, pool) -> bool | None:
    with database.connect(args, pool=pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                """
                SELECT
                    r.name,
                    r.component1,
                    r.component2,
                    c1.roomid AS c1_roomid,
                    c2.roomid AS c2_roomid
                FROM murdermotel.weapon_recipe r
                LEFT JOIN murdermotel.map_item_room c1
                    ON c1.itemname = r.component1 AND c1.serial = 0
                LEFT JOIN murdermotel.map_item_room c2
                    ON c2.itemname = r.component2 AND c2.serial = 0
                ORDER BY r.name
                """
            )
            cur.execute(q)
            for rec in database.resultiter(cur):
                c1_loc = f"#{rec['c1_roomid']}" if rec["c1_roomid"] else "unplaced"
                c2_loc = f"#{rec['c2_roomid']}" if rec["c2_roomid"] else "unplaced"
                io.echo(
                    f"{rec['name']}: {rec['component1']} ({c1_loc}) + {rec['component2']} ({c2_loc})"
                )
    return True
