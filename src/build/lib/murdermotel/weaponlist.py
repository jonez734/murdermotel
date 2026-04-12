import ttyio5 as ttyio
import bbsengine5 as bbsengine


def init(args=None, **kw):
    return True


def access(args, op, **kw):
    return bbsengine.checksysop(args)


def main(args, **kw):
    dbh = bbsengine.databaseconnect(args)
    sql = "select item.type, item.name, playground.roomid, playground.title as playgroundtitle, item.title as itemtitle from murdermotel.map_item_room as map, murdermotel.item as item, murdermotel.playground where map.roomid = playground.roomid and map.itemname = item.name and item.type = 'component' order by item.name asc"
    dat = []
    cur = dbh.cursor()
    cur.execute(sql, dat)
    for rec in bbsengine.resultiter(cur):
        ttyio.echo(
            f"{rec['name']} ({rec['type']}) is {rec['playgroundtitle']} (#{rec['roomid']})"
        )
        # ttyio.echo(f"{rec!r}", level="debug")
    return True
