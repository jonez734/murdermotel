import argparse
import copy
import random

from bbsengine6 import io, database, util, member, screen, module

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
    if self.args.debug is True:
      io.echo(f"{name}.load({self.classname})", level="debug")
    sql = f"select * from {self.table} where moniker=%s"
    dat = (name,)
    dbh = database.connect(self.args)
    cur = dbh.cursor()
#    ttyio.echo("%s.load.100: %r" % (self.classname, cur.mogrify(sql, dat)), level="debug")
    cur.execute(sql, dat)
    if cur.rowcount == 0:
      io.echo(f"unable to load record {name!r}", level="error")
      return False

    rec = cur.fetchone()
    for f in self.fields:
      setattr(self, f, rec[f])

    return True

  def save(self):
    p = {}
    for f in self.fields:
      p[f] = getattr(self, f)

    io.echo(f"{self.classname}.save.100: p={p!r}", level="debug")

    dbh = database.connect(self.args)
    if self.args.debug is True:
      io.echo(f"{self.classname}.save.120: trying update", level="debug")
    res = database.update(args, self.table, self.name, p, primarykey="moniker", mogrify=True)
    if self.args.debug is True:
      io.echo(f"{classname}.save.140: res={res!r}", level="debug")
    if res == 0:
      if self.args.debug is True:
        io.echo(f"{self.classname}.save.160: update failed, trying insert. p={p!r}", level="debug")
      database.insert(args, self.table, p, primarykey="name", returnid=False, mogrify=True)
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
        io.echo("Room.finditem.100: items={self.items!r} shortname={shortname}", level="debug")
      for x in range(0, len(self.items)):
        if self.items[x].name == shortname:
          return x
      return None

    def load(self, roomid) -> bool:
      if self.args.debug is True:
        io.echo(f"Room.load({roomid})", level="debug")
      sql = "select * from murdermotel.playground where roomid=%s"
      dat = (roomid,)
      dbh = database.connect(self.args)
      cur = dbh.cursor()
      if self.args.debug is True:
        io.echo("room.load.100: %r" % (cur.mogrify(sql, dat)), level="debug")
      cur.execute(sql, dat)
      if cur.rowcount == 0:
        io.echo(f"unable to load room {roomid!r}", level="error")
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
        io.echo(f"Room.save.100: r={r!r}", level="debug")

      dbh = database.connect(self.args)
      if self.args.debug is True:
        io.echo("Room.save.140: trying update", level="debug")
      res = database.update(args, "murdermotel.playground", self.roomid, r, primarykey="roomid", mogrify=mogrify)
      if self.args.debug is True:
        io.echo("Room.save.120: res=%r" % (res), level="debug")
      if res == 0:
        if self.args.debug is True:
          io.echo("Room.save.160: update failed, trying insert r=%r" % (r), level="debug")
        database.insert(args, "murdermotel.playground", r, primarykey="roomid", returnid=False, mogrify=mogrify)
      self.isdirty = False

      cur = dbh.cursor()
      sql = "delete from murdermotel.map_item_room where roomid=%s"
      dat = (self.roomid,)
      if mogrify is True and self.args.debug is True:
        io.echo(cur.mogrify(sql, dat), level="debug")
      cur.execute(sql, dat)
      for i in self.items:
        if self.args.debug is True:
          io.echo(f"Room.save.200: saving room item {i.name}", level="debug")
        m = {}
        m["itemname"] = i.name
        m["roomid"] = self.roomid
        database.insert(args, "murdermotel.map_item_room", m, returnid=False, mogrify=mogrify)

      dbh.commit()
      return True

class Living(object):
  def __init__(self, args):
    self.args = args
    self.roomid = None
  def short(self):
    return "NEEDINFO.living"
    
class Item(object):
  def __init__(self, args):
    super().__init__()
    self.roomid = None
  def short(self):
    return "NEEDINFO.item"

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
  def short(self):
    return "Thief"

class BoobyTrap(Item):
  def __init__(self, args):
    super().__init__(args)
    self.healthpoints = 20
    self.roomid = random.randint(10, getroomcount(args)-10+1)
    self.playerid = None

  def short(self):
    return ":mousetrap: Booby-Trap"

class Player(Living):
    def __init__(self, args):
      super().__init__(args)
      self.fields = ("moniker", "roomid", "turn", "moves", "memberid", "datelastplayed", "points", "bodycount")
      self.args = args
      self.moniker = member.getcurrentmoniker(args) # getmembername(args)
      self.turn = 1
      self.moves = MOVESPERTURN
      self.datelastplayed = "now()"
      self.memberid = member.getcurrentid(args) # getcurrentmemberid(args)
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
      buf = f"{self.moniker} ({status} {self.moves} {self.turn})"
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
        ["chlorine", "chlorinegas",    "gassprayer"],
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
        
          io.echo(f"complete weapon {name!r} found. i1={i1!r} i2={i2!r}", level="debug")
          w.append(name + " (weapon)")
      return w

    def finditem(self, shortname):
      if self.args.debug is True:
        io.echo(f"Room.finditem.100: items={self.items!r} shortname={shortname}", level="debug")
      for x in range(0, len(self.items)):
        if self.args.debug is True:
          io.echo(f"room.finditem.120: name={self.items[x].name}", level="debug")
        if self.items[x].name == shortname:
          return x
      return None

    def load(self, moniker) -> bool:
      if self.args.debug is True:
        io.echo(f"Player.load({moniker!r})", level="debug")
      sql = "select * from murdermotel.player where moniker=%s"
      dat = (moniker,)
      dbh = database.connect(self.args)
      cur = dbh.cursor()
      if self.args.debug is True:
        io.echo(f"player.load.100: {cur.mogrify(sql, dat)!r}", level="debug")
      cur.execute(sql, dat)
      if cur.rowcount == 0:
        if self.args.debug is True:
          io.echo(f"unable to load player {name!r}", level="debug")
        return False

      rec = cur.fetchone()
      for f in self.fields:
        setattr(self, f, rec[f])
        
      self.items = getplayeritems(self.args, self.moniker)
      
      return True

    def save(self, mogrify=False):
      if self.args.debug is True:
        io.echo(f"self.memberid={self.memberid}", level="debug")
      p = {}
      for f in self.fields:
        p[f] = getattr(self, f)

      if self.args.debug is True:
        io.echo(f"Player.save.100: p={p!r}", level="debug")

      if self.args.debug is True:
        io.echo("Player.save.140: trying update", level="debug")
      res = database.update(self.args, "murdermotel.player", self.moniker, p, primarykey="moniker", mogrify=mogrify)
      if self.args.debug is True:
        io.echo(f"Player.save.120: res={res!r}", level="debug")
      if res == 0:
        if self.args.debug is True:
          io.echo(f"Player.save.160: update failed, trying insert p={p!r}", level="debug")
        database.insert(self.args, "murdermotel.player", p, primarykey="moniker", returnid=False, mogrify=mogrify)

      dbh = database.connect(self.args)
      cur = dbh.cursor()
      sql = "delete from murdermotel.map_item_player where playermoniker=%s"
      dat = (self.moniker,)
      if mogrify is True and self.args.debug is True:
        io.echo(cur.mogrify(sql, dat), level="debug")
      cur.execute(sql, dat)
      for i in self.items:
        if self.args.debug is True:
          io.echo(f"Player.save.200: saving player item {i.name!r}", level="debug")
        m = {}
        m["itemname"] = i.name
        m["playermoniker"] = self.moniker
        database.insert(self.args, "murdermotel.map_item_player", m, returnid=False, mogrify=True)
        
      database.commit(self.args)
      return True

    def info(self):
      io.echo(f"{{var:labelcolor}}Moves: {{var:valuecolor}}{self.moves}")
      io.echo(f"{{var:labelcolor}}Turns: {{var:valuecolor}}{self.turn}")
      io.echo(f"{{var:labelcolor}}Name:  {{var:valuecolor}}{self.moniker}")
      date = util.datestamp(self.datelastplayed)
      io.echo(f"{{var:labelcolor}}Date:  {{var:valuecolor}}{date}")
      items = copy.deepcopy(self.items)
      items = self.weapons(items)+items
      util.oxfordcomma(items)
      io.echo(f"{{var:labelcolor}}Items: {{var:valuecolor}}{items}")
    
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
        
          io.echo(f"complete weapon {name!r} found. i1={i1!r} i2={i2!r}", level="debug")
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
      io.echo(f"weapons={w!r}", level="debug")
      return w + items

currentplayer = None
def setcurrentplayer(player):
  global currentplayer
  currentplayer = player

def getcurrentplayer():
  global currentplayer
  return currentplayer

class completeItemName(object):
    def __init__(self, args, **kw):
      self.roomid = kw["roomid"] if "roomid" in kw else None
      self.playermoniker = kw["playermoniker"] if "playermoniker" in kw else None

      self.args = args
      
      if self.args.debug is True:
        io.echo(f"completeItemName.100: kw={kw}", level="debug")

    def complete(self:object, text:str, state:int):
      if self.args.debug is True:
        io.echo("completeItemName.140: complete called", level="debug")

      if self.args.debug is True:
        io.echo(f"completeItemName.160: building vocab. self.roomid={self.roomid!r}, self.playermoniker={self.playermoniker!r}", level="debug")

      if self.roomid is not None:
        sql = "select name from murdermotel.item as i, murdermotel.map_item_room as m where i.name = m.itemname and m.roomid=%s"
        dat = (self.roomid,)
      elif self.playermoniker is not None:
        sql = "select name from murdermotel.item as i, murdermotel.map_item_player as m where i.name = m.itemname and m.playermoniker=%s"
        dat = (self.playermoniker,)
      else:
        sql = "select name from murdermotel.item as i"
        dat = ()
        
      dbh = database.connect(self.args)
      cur = dbh.cursor()
      if self.args.debug is True:
        io.echo(f"completeItemName.120: mogrify={cur.mogrify(sql, dat)!r}")
      cur.execute(sql, dat)

      vocab = []
      for rec in util.resultiter(cur):
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
      io.echo(f"Item.save.100: p={p!r}", level="debug")

    if self.args.debug is True:
      io.echo("Item.save.140: trying update", level="debug")
    res = database.update(self.args, "murdermotel.item", self.name, p, primarykey="name", mogrify=True)
    io.echo(f"Item.save.120: res={res!r}", level="debug")
    if res == 0:
      if self.args.debug is True:
        io.echo(f"Item.save.160: update failed, trying insert p={p!r}", level="debug")
      database.insert(self.args, "murdermotel.item", p, primarykey="name", returnid=False, mogrify=True)
    database.commit(self.args)
    return True

def setarea(args, player, left, **kw):
    # ttyio.echo(f"kw={kw!r}")
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

          turn = " | %s" % (util.pluralize(4-player.turn, "turn", "turns"))

          if player.roomid is not None:
            room = f" | room #{player.roomid}"
            currentroom = getroom(args, player.roomid)
            if currentroom is not None and currentroom.shortname is not None:
              room += " "+currentroom.shortname
          else:
            room = ""

          moves = " | %s" % (util.pluralize(player.moves, "move", "moves"))
          
          playername = f" | {isdirty}{player.moniker}"

        buf += f"{playername}{room}{turn}{moves}{debug}{help}"

        return buf

    screen.setarea(left, right)
    return

def init(args=None):
#  ttyio.setvariable("optioncolor", "{white}{bggray}")
#  ttyio.setvariable("menudesc", "{/bgcolor}{white}")
#  ttyio.setvariable("valuecolor", "{/bgcolor}{green}")
#  ttyio.setvariable("promptcolor", "{/bgcolor}{lightgray}")
#  ttyio.setvariable("inputcolor", "{/bgcolor}{green}")
  return True

# @since 20220813
def runmodule(args, submodule, **kw):
#  io.echo("mudermotel.lib.runsubmodule.120: trace") # , level="debug", end="\n")
  x = f"{PACKAGENAME}.{submodule}"
  if args.debug is True:
    io.echo("lib.runsubmodule.100: x=%r" % (x), level="debug")
  return module.runmodule(args, x, **kw)

def buildargs(args=None, **kw):
    parser = argparse.ArgumentParser("murdermotel")

    parser.add_argument("--verbose", action="store_true", dest="verbose")
    parser.add_argument("--debug", action="store_true", dest="debug")
    parser.add_argument("--terminalwidth", action="store", dest="terminalwidth", default=io.getterminalwidth())
    parser.add_argument("--node", action="store", dest="node", default="cyclops")

    defaults = {"databasename": "zoid6", "databasehost":"localhost", "databaseuser": None, "databaseport":5432, "databasepassword":None}
    database.buildargdatabasegroup(parser, defaults)
    return parser

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
  sql = "select * from murdermotel.playground where roomid=%s"
  dat = (roomid,)
  dbh = database.connect(args)
  cur = dbh.cursor()
  cur.execute(sql, dat)
  if cur.rowcount == 0:
    return None

  res = cur.fetchone()

  return buildroomob(args, res)

def getroomcount(args):
  dbh = database.connect(args)
  sql = "select count(roomid) from murdermotel.playground"
  dat = ()
  cur = dbh.cursor()
  cur.execute(sql)
  if cur.rowcount == 0:
    io.echo("no rooms in the playground. notify sysop.", level="error")
    return None
  return cur.fetchone()["count"]

# @since 20220921
def getroomitems(args, roomid, mogrify=True):
  sql = "select * from murdermotel.item as i, murdermotel.map_item_room as m where m.roomid = %s and m.itemname = i.name"
  dat = (roomid,)
  dbh = database.connect(args)
  cur = dbh.cursor()
  cur.execute(sql, dat)
  if mogrify is True and args.debug is True:
    io.echo("getroomitems.100: %s" % (cur.mogrify(sql, dat)), level="debug")

  if cur.rowcount == 0:
    return []

  items = []
  for rec in database.resultiter(cur):
    i = Item(args)
    i.name = rec["name"]
    i.title = rec["title"]
    i.type = rec["type"]
    i.usemessages = rec["usemessages"] if "usemessages" in rec else []
    items.append(i)
  return items

def getplayeritems(args, playername, mogrify=True):
  if args.debug is True:
    io.echo("getplayeritems.100: foo", level="debug")
  sql = "select * from murdermotel.item as i, murdermotel.map_item_player as m where m.playermoniker = %s and m.itemname = i.name"
  dat = (playername,)
  dbh = database.connect(args)
  cur = dbh.cursor()
  cur.execute(sql, dat)
  if mogrify is True and args.debug is True:
    io.echo("getplayeritems.100: %s" % (cur.mogrify(sql, dat)), level="debug")

  if cur.rowcount == 0:
    return []

  items = []
  for rec in database.resultiter(cur):
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
  dbh = database.connect(args)
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
  sql = "select moniker from murdermotel.player as p where p.roomid=%s"
  dat = (roomid,)

  dbh = database.connect(args)
  cur = dbh.cursor()
  if mogrify is True:
    io.echo("mm.lib.getroomplayers.100: %s" % (cur.mogrify(sql, dat)), level="debug")
  cur.execute(sql, dat)
  players = []
  if cur.rowcount > 0:
    for rec in database.resultiter(cur):
      p = Player(args)
      p.load(rec["moniker"])
      players.append(p)

  return players
