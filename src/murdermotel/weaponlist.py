from bbsengine6 import bbsengine, database, io


def init(args=None, **kw):
    return True


def access(args, op, **kw):
    return bbsengine.checksysop(args)


def buildargs(args, **kw):
    return None


def main(args, **kw):
    pool = kw.get("pool", None)
    if pool is None:
        io.echo(f"mm.weaponlist.main.100: {pool=}", level="error")
        return False

    sql = "select item.kind, item.name, item.serial, playground.roomid, playground.title as playgroundtitle, item.title as itemtitle from murdermotel.map_item_room as map, murdermotel.item as item, murdermotel.playground where map.roomid = playground.roomid and map.itemname = item.name and map.serial = item.serial and item.kind = 'component' order by item.name, item.serial asc"
    dat = []
    with database.connect(args, pool=pool) as conn:
        with database.cursor(conn) as cur:
            cur.execute(sql, dat)
            for rec in database.resultiter(cur):
                io.echo(
                    f"{rec['name']}-{rec['serial']} ({rec['kind']}) is {rec['playgroundtitle']} (#{rec['roomid']})"
                )
    return True
