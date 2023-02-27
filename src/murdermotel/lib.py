import copy
import random

import ttyio5 as ttyio
import bbsengine5 as bbsengine

# @since 20220813
PACKAGENAME = "murdermotel"
MOVESPERTURN = 60
TURNSPERDAY = 2
PLAYGROUNDSIZE = 140
MAXITEMSPERPLAYER = 5

class Obj(object):
  def __init__(self, args):
    self.args = args
    self.table = "murdermotel.player"
    self.fields = ()
    self.classname = self.__class__.__name__

  def load(self, name) -> bool:
    ttyio.echo("%s.load({self.classname})", level="debug")
    sql = "select * from %s where name=%%s" % (self.table)
    dat = (name,)
    dbh = bbsengine.databaseconnect(self.args)
    cur = dbh.cursor()
#    ttyio.echo("%s.load.100: %r" % (self.classname, cur.mogrify(sql, dat)), level="debug")
    cur.execute(sql, dat)
    if cur.rowcount == 0:
      ttyio.echo("unable to load record %r" % (name), level="error")
      return False

    rec = cur.fetchone()
    for f in self.fields:
      setattr(self, f, rec[f])

    return True

  def save(self):
    p = {}
    for f in self.fields:
      p[f] = getattr(self, f)

    ttyio.echo(f"{self.classname}.save.100: p={p!r}", level="debug")

    dbh = bbsengine.databaseconnect(self.args)
    if self.args.debug is True:
      ttyio.echo(f"{classname}.save.140: trying update", level="debug")
    res = bbsengine.update(dbh, self.table, self.name, p, primarykey="name", mogrify=True)
    if self.args.debug is True:
      ttyio.echo("{classname}.save.120: res={res!r}", level="debug")
    if res == 0:
      if self.args.debug is True:
        ttyio.echo("%s.save.160: update failed, trying insert. p=%r" % (p), level="debug")
      bbsengine.insert(dbh, self.table, p, primarykey="name", returnid=False, mogrify=True)
    self.isdirty = False
    dbh.commit()
    return True

class Room(object):
    def __init__(self, args): # , name, location, description):
      self.fields = ("shortname", "roomid", "title")
      self.args = args
      self.shortname = None
      self.roomid = None
      self.title = None
      self.items = []
      self.exits = {}
      self.table = "murdermotel.playground"

    def finditem(self, shortname):
      if self.args.debug is True:
        ttyio.echo("Room.finditem.100: items={self.items!r} shortname={shortname}", level="debug")
      for x in range(0, len(self.items)):
        if self.items[x].name == shortname:
          return x
      return None

    def load(self, roomid) -> bool:
      if self.args.debug is True:
        ttyio.echo(f"Room.load({roomid})", level="debug")
      sql = "select * from murdermotel.playground where roomid=%s"
      dat = (roomid,)
      dbh = bbsengine.databaseconnect(self.args)
      cur = dbh.cursor()
      if self.args.debug is True:
        ttyio.echo("room.load.100: %r" % (cur.mogrify(sql, dat)), level="debug")
      cur.execute(sql, dat)
      if cur.rowcount == 0:
        ttyio.echo(f"unable to load room {roomid!r}", level="error")
        return False

      rec = cur.fetchone()
      for f in self.fields:
        setattr(self, f, rec[f])

      for f in ("north", "south", "east", "west", "up", "down"):
        self.exits[f] = rec[f]
        
      self.items = getroomitems(self.args, roomid)

      return True

    def save(self, mogrify=False):
      r = {}
      for f in self.fields:
        r[f] = getattr(self, f)

      for e in ("north", "south", "east", "west", "up", "down"):
        r[e] = self.exits[e]

      if self.args.debug is True:
        ttyio.echo(f"Room.save.100: r={r!r}", level="debug")

      dbh = bbsengine.databaseconnect(self.args)
      if self.args.debug is True:
        ttyio.echo("Room.save.140: trying update", level="debug")
      res = bbsengine.update(dbh, "murdermotel.playground", self.roomid, r, primarykey="roomid", mogrify=mogrify)
      if self.args.debug is True:
        ttyio.echo("Room.save.120: res=%r" % (res), level="debug")
      if res == 0:
        if self.args.debug is True:
          ttyio.echo("Room.save.160: update failed, trying insert r=%r" % (r), level="debug")
        bbsengine.insert(dbh, "murdermotel.playground", r, primarykey="roomid", returnid=False, mogrify=mogrify)
      self.isdirty = False

      cur = dbh.cursor()
      sql = "delete from murdermotel.map_item_room where roomid=%s"
      dat = (self.roomid,)
      if mogrify is True and self.args.debug is True:
        ttyio.echo(cur.mogrify(sql, dat), level="debug")
      cur.execute(sql, dat)
      for i in self.items:
        if self.args.debug is True:
          ttyio.echo(f"Room.save.200: saving room item {i.name}", level="debug")
        m = {}
        m["itemname"] = i.name
        m["roomid"] = self.roomid
        bbsengine.insert(dbh, "murdermotel.map_item_room", m, returnid=False, mogrify=mogrify)

      dbh.commit()
      return True

class Living(object):
  def __init__(self, args):
    self.args = args
    self.roomid = None
  def short(self):
    return "NEEDINFO"
    
class Item(object):
  def __init__(self, args):
    super().__init__()
    self.roomid = None
  def short(self):
    return "NEEDINFO"

class RabidWolf(Living):
  def __init__(self, args):
    super().__init__(args)
    self.healthpoints = 35
    self.roomid = random.randint(10, getroomcount(args)-10)
  def short(self):
    return ":wolf: rabid wolf"

class Thief(Living):
  def __init__(self, args):
    super().__init__(args)
    self.healthpoints = 35
    self.roomid = random.randint(10, getroomcount(args)-10)
    self.items = []

class BoobyTrap(Item):
  def __init__(self):
    super().__init__()
  def short(self):
    return "Booby-Trap"

class Player(Living):
    def __init__(self, args):
      super().__init__(args)
      self.fields = ("name", "roomid", "turn", "moves", "memberid", "datelastplayed", "points", "bodycount")
      self.args = args
      self.name = bbsengine.getmembername(args)
      self.turn = 1
      self.moves = MOVESPERTURN
      self.datelastplayed = "now()"
      self.memberid = bbsengine.getcurrentmemberid(args)
      self.items = []
      self.isdirty = False
      self.points = 0
      self.bodycount = 0

    def __repr__(self):
      buf = ""
      for f in self.fields:
        buf += "%s=%r " % (f, getattr(self, f))
      return buf

    def __str__(self):
      status = "alive" if self.moves > 0 else "dead"
      buf = f"{self.name} ({status} {self.moves} {self.turn})"
      return buf

    def weapons(self, items=None):
      if items is None:
        items = copy.deepcopy(self.items)

      def find(shortname):
        for x in range(0, len(items)):
          if items[x].name == shortname:
            return x
        return None

      components = [
        ["axe",      "axeblade",       "axehandle"],
        ["pistol",   "pistol",         "bullets"],
        ["chlorine", "chlorine",       "gassprayer"],
        ["fire",     "lighterfluid",   "flamethrower"],
        ["acid",     "industrialacid", "acidsprayer"],
      ]
      
      w = []
      for fortytwo in components:
        name = fortytwo[0]
        c1 = fortytwo[1]
        c2 = fortytwo[2]

        if find(c1) is not None and find(c2) is not None:
          i1 = find(c1)
          if i1 is not None:
            del items[i1]

          i2 = find(c2)
          if i2 is not None:
            del items[i2]
        
          ttyio.echo(f"complete weapon {name!r} found. i1={i1!r} i2={i2!r}", level="debug")
          w.append(name + " (weapon)")
      return w

    def finditem(self, shortname):
      ttyio.echo(f"Room.finditem.100: items={self.items!r} shortname={shortname}", level="debug")
      for x in range(0, len(self.items)):
        ttyio.echo(f"room.finditem.120: name={self.items[x].name}", level="debug")
        if self.items[x].name == shortname:
          return x
      return None

    def load(self, name) -> bool:
      if self.args.debug is True:
        ttyio.echo(f"Player.load({name!r})", level="debug")
      sql = "select * from murdermotel.player where name=%s"
      dat = (name,)
      dbh = bbsengine.databaseconnect(self.args)
      cur = dbh.cursor()
      if self.args.debug is True:
        ttyio.echo(f"player.load.100: {cur.mogrify(sql, dat)!r}", level="debug")
      cur.execute(sql, dat)
      if cur.rowcount == 0:
        if self.args.debug is True:
          ttyio.echo(f"unable to load player {name!r}", level="debug")
        return False

      rec = cur.fetchone()
      for f in self.fields:
        setattr(self, f, rec[f])
        
      self.items = getplayeritems(self.args, self.name)
      
      return True

    def save(self, mogrify=False):
      if self.args.debug is True:
        ttyio.echo(f"self.memberid={self.memberid}", level="debug")
      p = {}
      for f in self.fields:
        p[f] = getattr(self, f)

      if self.args.debug is True:
        ttyio.echo(f"Player.save.100: p={p}", level="debug")

      dbh = bbsengine.databaseconnect(self.args)
      
      if self.args.debug is True:
        ttyio.echo("Player.save.140: trying update", level="debug")
      res = bbsengine.update(dbh, "murdermotel.player", self.name, p, primarykey="name", mogrify=mogrify)
      if self.args.debug is True:
        ttyio.echo("Player.save.120: res=%r" % (res), level="debug")
      if res == 0:
        if self.args.debug is True:
          ttyio.echo("Player.save.160: update failed, trying insert p=%r" % (p), level="debug")
        bbsengine.insert(dbh, "murdermotel.player", p, primarykey="name", returnid=False, mogrify=mogrify)

      cur = dbh.cursor()
      sql = "delete from murdermotel.map_item_player where playername=%s"
      dat = (self.name,)
      if mogrify is True and self.args.debug is True:
        ttyio.echo(cur.mogrify(sql, dat), level="debug")
      cur.execute(sql, dat)
      for i in self.items:
        if self.args.debug is True:
          ttyio.echo("Player.save.200: saving player item %r" % (i.name), level="debug")
        m = {}
        m["itemname"] = i.name
        m["playername"] = self.name
        bbsengine.insert(dbh, "murdermotel.map_item_player", m, returnid=False, mogrify=True)
        
      dbh.commit()
      return True

    def info(self):
      ttyio.echo(f"{{var:labelcolor}}Moves: {{var:valuecolor}}{self.moves}")
      ttyio.echo(f"{{var:labelcolor}}Turns: {{var:valuecolor}}{self.turn}")
      ttyio.echo(f"{{var:labelcolor}}Name:  {{var:valuecolor}}{self.name}")
      date = bbsengine.datestamp(self.datelastplayed)
      ttyio.echo(f"{{var:labelcolor}}Date:  {{var:valuecolor}}{date}")
      items = copy.deepcopy(self.items)
      items = self.weapons(items)+items
      bbsengine.oxfordcomma(items)
      ttyio.echo(f"{{var:labelcolor}}Items: {{var:valuecolor}}{items}")
    
    def getitems(self):
      items = copy.deepcopy(self.items)
      def findcomponent(shortname):
        # ttyio.echo(f"getitems.findcomponent.100: items={self.items!r} shortname={shortname}", level="debug")
        for x in range(0, len(items)):
          # ttyio.echo(f"getitems.findcomponent.120: name={items[x].name}", level="debug")
          if items[x].name == shortname:
            return x
        return None

      return self.weapons(items) + items
      w = []

      components = [
        ["axe",      "axeblade",       "axehandle"],
        ["pistol",   "pistol",         "bullets"],
        ["chlorine", "chlorine",       "gassprayer"],
        ["fire",     "lighterfluid",   "flamethrower"],
        ["acid",     "industrialacid", "acidsprayer"],
      ]
      for fortytwo in components:
        # ttyio.echo(f"getitems.100: fortytwo={fortytwo!r}", level="debug")
        name = fortytwo[0]

        c1 = fortytwo[1]
        c2 = fortytwo[2]

        if findcomponent(c1) is not None and findcomponent(c2) is not None:
          i1 = findcomponent(c1)
          if i1 is not None:
            del items[i1]

          i2 = findcomponent(c2)
          if i2 is not None:
            del items[i2]
        
          ttyio.echo(f"complete weapon {name!r} found. i1={i1!r} i2={i2!r}", level="debug")
          w.append(name + " (weapon)")

#      if self.finditem("pistol") and self.finditem("bullets"):
#          w.append("pistol")
#          del items["pistol"]
#          del items["bullets"]
#      if self.finditem("chlorine") and self.finditem("gassprayer"):
#          w.append("chlorine")
#          del items["chlorine"]
#          del items["gassprayer"]
#      if self.finditem("lighterfluid") and self.finditem("flamethrower"):
#          w.append("fire")
#          del items["lighterfluid"]
#          del items["flamethrower"]
#      if self.finditem("industrialacid") and self.finditem("acidsprayer"):
#          w.append("acid")
#          del items["industrialacid"]
#          del items["acidsprayer"]
      ttyio.echo(f"weapons={w!r}", level="debug")
      return w + items

class completeItemName(object):
    def __init__(self, args, **kw):
      self.roomid = kw["roomid"] if "roomid" in kw else None
      self.playername = kw["playername"] if "playername" in kw else None

      self.args = args
      
      if self.args.debug is True:
        ttyio.echo(f"completeItemName.100: kw={kw}", level="debug")

    def complete(self:object, text:str, state:int):
      if self.args.debug is True:
        ttyio.echo("completeItemName.140: complete called", level="debug")

      dbh = bbsengine.databaseconnect(self.args)

      if self.args.debug is True:
        ttyio.echo(f"completeItemName.160: building vocab. self.roomid={self.roomid!r}, self.playername={self.playername!r}", level="debug")
      vocab = []
      if self.roomid is not None:
        sql = "select name from murdermotel.item as i, murdermotel.map_item_room as m where i.name = m.itemname and m.roomid=%s"
        dat = (self.roomid,)
      elif self.playername is not None:
        sql = "select name from murdermotel.item as i, murdermotel.map_item_player as m where i.name = m.itemname and m.playername=%s"
        dat = (self.playername,)
      else:
        sql = "select name from murdermotel.item as i"
        dat = ()
        
      cur = dbh.cursor()
      if self.args.debug is True:
        ttyio.echo(f"completeItemName.120: mogrify={cur.mogrify(sql, dat)}")
      cur.execute(sql, dat)

      for rec in bbsengine.resultiter(cur):
        vocab.append(rec["name"])

      results = [x for x in vocab if x.startswith(text)] + [None]
      return results[state]

class Item(object):
  def __init__(self, args):
    self.fields = ("type", "name", "title", "usemessages")
    self.args = args
    self.type = None
    self.name = None # primary key
    self.title = None
    self.usemessages = []
  
  def __repr__(self):
    return f"{self.title} ({self.type})"

  def save(self):
    p = {}
    for f in self.fields:
      p[f] = getattr(self, f)

    if self.args.debug is True:
      ttyio.echo(f"Item.save.100: p={p!r}", level="debug")

    dbh = bbsengine.databaseconnect(self.args)
    if self.args.debug is True:
      ttyio.echo("Item.save.140: trying update", level="debug")
    res = bbsengine.update(dbh, "murdermotel.item", self.name, p, primarykey="name", mogrify=True)
    ttyio.echo(f"Item.save.120: res={res!r}", level="debug")
    if res == 0:
      if self.args.debug is True:
        ttyio.echo(f"Item.save.160: update failed, trying insert p={p!r}", level="debug")
      bbsengine.insert(dbh, "murdermotel.item", p, primarykey="name", returnid=False, mogrify=True)
    dbh.commit()
    return True

class BoobyTrap(Item):
  def __init__(self, args):
    super().__init__(args)
    self.healthpoints = 20
    self.roomid = random.randint(10, getroomcount(args)-10+1)

def setarea(args, player, left, **kw):
    ttyio.echo(f"kw={kw!r}")
    def right():
        help = " | F1: Help" if "help" in kw and kw["help"] is True else ""
        debug = " | debug" if args.debug is True else ""
        room = ""
        playername = ""
        moves = ""
        turn = ""

        buf = "murder motel"
        if player is not None:
          if player.isdirty is True:
              isdirty = "*"
          else:
              isdirty = ""

          turn = " | %s" % (bbsengine.pluralize(4-player.turn, "turn", "turns"))

          if player.roomid is not None:
            room = f" | room #{player.roomid}"
            currentroom = getroom(args, player.roomid)
            if currentroom is not None and currentroom.shortname is not None:
              room += " "+currentroom.shortname
          else:
            room = ""

          moves = " | %s" % (bbsengine.pluralize(player.moves, "move", "moves"))
          
          playername = f" | {isdirty}{player.name}"

        buf += f"{playername}{room}{turn}{moves}{debug}{help}"

        return buf

    bbsengine.setarea(left, right)
    return

def init(args=None):
  ttyio.setvariable("optioncolor", "{white}{bggray}")
  ttyio.setvariable("menudesc", "{/bgcolor}{white}")
  ttyio.setvariable("valuecolor", "{/bgcolor}{green}")
  ttyio.setvariable("promptcolor", "{/bgcolor}{lightgray}")
  ttyio.setvariable("inputcolor", "{/bgcolor}{green}")

# @since 20220813
def runsubmodule(args, player, submodule, **kw):
  x = f"{PACKAGENAME}.{submodule}"
  if args.debug is True:
    ttyio.echo("lib.runsubmodule.100: x=%r" % (x), level="debug")
  return bbsengine.runsubmodule(args, x, player=player, **kw)

def buildroomdict(res):
  room = {}
  for f in ("north", "south", "east", "west", "up", "down", "title", "shortname"):
    room[f] = res[f] if f in res else None
  return room

def buildroomob(args, res):
  room = Room(args)
  roomid = res["roomid"]
  room.load(roomid)
  return room

def getroom(args, roomid):
  dbh = bbsengine.databaseconnect(args)
  sql = "select * from murdermotel.playground where roomid=%s"
  dat = (roomid,)
  cur = dbh.cursor()
  cur.execute(sql, dat)
  if cur.rowcount == 0:
    return None

  res = cur.fetchone()

  return buildroomob(args, res)

def getroomcount(args):
  dbh = bbsengine.databaseconnect(args)
  sql = "select count(roomid) from murdermotel.playground"
  dat = ()
  cur = dbh.cursor()
  cur.execute(sql)
  if cur.rowcount == 0:
    ttyio.echo("no rooms in the playground. notify sysop.", level="error")
    return None
  return cur.fetchone()["count"]

# @since 20220921
def getroomitems(args, roomid, mogrify=True):
  sql = "select * from murdermotel.item as i, murdermotel.map_item_room as m where m.roomid = %s and m.itemname = i.name"
  dat = (roomid,)
  dbh = bbsengine.databaseconnect(args)
  cur = dbh.cursor()
  cur.execute(sql, dat)
  if mogrify is True and args.debug is True:
    ttyio.echo("getroomitems.100: %s" % (cur.mogrify(sql, dat)), level="debug")

  if cur.rowcount == 0:
    return []

  items = []
  for rec in bbsengine.resultiter(cur):
    i = Item(args)
    i.name = rec["name"]
    i.title = rec["title"]
    i.type = rec["type"]
    i.usemessages = rec["usemessages"] if "usemessages" in rec else []
    items.append(i)
  return items

def getplayeritems(args, playername, mogrify=True):
  if args.debug is True:
    ttyio.echo("getplayeritems.100: foo", level="debug")
  sql = "select * from murdermotel.item as i, murdermotel.map_item_player as m where m.playername = %s and m.itemname = i.name"
  dat = (playername,)
  dbh = bbsengine.databaseconnect(args)
  cur = dbh.cursor()
  cur.execute(sql, dat)
  if mogrify is True and args.debug is True:
    ttyio.echo("getplayeritems.100: %s" % (cur.mogrify(sql, dat)), level="debug")

  if cur.rowcount == 0:
    return []

  items = []
  for rec in bbsengine.resultiter(cur):
    i = Item(args)
    i.type = rec["type"]
    i.name = rec["name"]
    i.title = rec["title"]
    i.usemessages = rec["usemessages"] if "usemessages" in rec else []
    items.append(i)
  return items

def getitem(args, name):
  sql = "select * from murdermotel.item as i where name=%s"
  dat = (name,)
  dbh = bbsengine.databaseconnect(args)
  cur = dbh.cursor()
  cur.execute(sql, dat)
  if cur.rowcount == 0:
    return None
  i = Item(args)
  i.type = rec["type"]
  i.name = rec["name"]
  i.title = rec["title"]
  i.usemessages = rec["usemessages"] if "usemessages" in rec else []

def getroomplayers(args, roomid, mogrify=True):
  sql = "select name from murdermotel.player as p where p.roomid=%s"
  dat = (roomid,)

  dbh = bbsengine.databaseconnect(args)
  cur = dbh.cursor()
  if mogrify is True:
    ttyio.echo("mm.lib.getroomplayers.100: %s" % (cur.mogrify(sql, dat)), level="debug")
  cur.execute(sql, dat)
  players = []
  if cur.rowcount > 0:
    for rec in bbsengine.resultiter(cur):
      p = Player(args)
      p.load(rec["name"])
      players.append(p)

  return players
