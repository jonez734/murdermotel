import time
import locale

from bbsengine6 import io, database

from . import lib

def init(args=None, **kw):
  return True

def access(args, op, **kw):
  return bbsengine.checksysop(args)

def buildargs(args, **kw):
  return None

def main(args, **kw):
    dbh = database.connect(args)
    sql = "select item.type, item.name, playground.roomid, playground.title as playgroundtitle, item.title as itemtitle from murdermotel.map_item_room as map, murdermotel.item as item, murdermotel.playground where map.roomid = playground.roomid and map.itemname = item.name and item.type = 'component' order by item.name asc"
    dat = []
    cur = dbh.cursor()
    cur.execute(sql, dat)
    for rec in database.resultiter(cur):
      io.echo(f"{rec['name']} ({rec['type']}) is {rec['playgroundtitle']} (#{rec['roomid']})")
      # ttyio.echo(f"{rec!r}", level="debug")
    return True
