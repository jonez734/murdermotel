import ttyio5 as ttyio
import bbsengine5 as bbsengine

# @since 20220813
PACKAGENAME = "murdermotel"
MOVESPERTURN = 60
TURNSPERDAY = 2
PLAYGROUNDSIZE = 140

class Obj(object):
  def __init__(self, args):
    self.args = args
    self.table = "murdermotel.player"
    self.fields = ()
    self.classname = self.__class__.__name__

  def load(self, name) -> bool:
    ttyio.echo("%s.load(%r)" % (self.classname), level="debug")
    sql = "select * from %s where name=%%s" % (self.table)
    dat = (name,)
    dbh = bbsengine.databaseconnect(self.args)
    cur = dbh.cursor()
    ttyio.echo("%s.load.100: %r" % (self.classname, cur.mogrify(sql, dat)), level="debug")
    cur.execute(sql, dat)
    if cur.rowcount == 0:
      ttyio.echo("unable to load record %r" % (name), level="debug")
      return False

    rec = cur.fetchone()
    for f in self.fields:
      setattr(self, f, rec[f])

    return True

  def save(self):
    p = {}
    for f in self.fields:
      p[f] = getattr(self, f)

    ttyio.echo("%s.save.100: p=%r" % (self.classname, p), level="debug")

    dbh = bbsengine.databaseconnect(self.args)
    ttyio.echo("%s.save.140: trying update" % (classname), level="debug")
    res = bbsengine.update(dbh, self.table, self.name, p, primarykey="name", mogrify=True)
    ttyio.echo("%s.save.120: res=%r" % (res), level="debug")
    if res is None:
      ttyio.echo("%s.save.160: update failed, trying insert. p=%r" % (p), level="debug")
      bbsengine.insert(dbh, self.table, p, primarykey="name", returnid=False, mogrify=True)
    self.isdirty = False
    dbh.commit()
    return True

class WeaponComponent(object):
    def __init__(self, args, name, location, description):
        self.args = args
        self.name = name
        self.description = description
        self.location = location

class Safety(object):
    def __init__(self, args, name, location, description):
        self.args = args
        self.name = name
        self.location = location
        self.description = description

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

    def load(self, roomid) -> bool:
      ttyio.echo("Room.load(%r)" % (roomid), level="debug")
      sql = "select * from murdermotel.playground where roomid=%s"
      dat = (roomid,)
      dbh = bbsengine.databaseconnect(self.args)
      cur = dbh.cursor()
      ttyio.echo("room.load.100: %r" % (cur.mogrify(sql, dat)), level="debug")
      cur.execute(sql, dat)
      if cur.rowcount == 0:
        ttyio.echo("unable to load room %r" % (roomid), level="debug")
        return False

      rec = cur.fetchone()
      for f in self.fields:
        setattr(self, f, rec[f])

      for f in ("north", "south", "east", "west", "up", "down"):
        self.exits[f] = rec[f]

      return True

    def save(self):
      r = {}
      for f in self.fields:
        r[f] = getattr(self, f)

      for e in ("north", "south", "east", "west", "up", "down"):
        r[e] = self.exits[e]

      ttyio.echo("Room.save.100: r=%r" % (r), level="debug")

      dbh = bbsengine.databaseconnect(self.args)
      ttyio.echo("Room.save.140: trying update", level="debug")
      res = bbsengine.update(dbh, "murdermotel.playground", self.roomid, r, primarykey="roomid", mogrify=True)
      ttyio.echo("Room.save.120: res=%r" % (res), level="debug")
      if res is None:
        ttyio.echo("Room.save.160: update failed, trying insert r=%r" % (r), level="debug")
        bbsengine.insert(dbh, "murdermotel.playground", r, primarykey="roomid", returnid=False, mogrify=True)
      self.isdirty = False
      dbh.commit()
      return True

class Player(object):
    def __init__(self, args):
      self.fields = ("name", "roomid", "turn", "moves", "memberid", "datelastplayed")
      self.args = args
      self.name = bbsengine.getcurrentmembername(args)
      self.roomid = None
      self.isdirty = False
      self.turn = 1
      self.moves = MOVESPERTURN
      self.datelastplayed = "now()"
      self.memberid = bbsengine.getcurrentmemberid(args)
      self.table = "murdermotel.player"

    def __repr__(self):
      buf = ""
      for f in self.fields:
        buf += "%s=%r " % (f, getattr(self, f))
      return buf

    def load(self, name) -> bool:
      ttyio.echo("Player.load(%r)" % (name), level="debug")
      sql = "select * from murdermotel.player where name=%s"
      dat = (name,)
      dbh = bbsengine.databaseconnect(self.args)
      cur = dbh.cursor()
      ttyio.echo("player.load.100: %r" % (cur.mogrify(sql, dat)), level="debug")
      cur.execute(sql, dat)
      if cur.rowcount == 0:
        ttyio.echo("unable to load player %r" % (name), level="debug")
        return False

      rec = cur.fetchone()
      for f in self.fields:
        setattr(self, f, rec[f])

      return True

    def save(self):
      ttyio.echo("self.memberid=%r" % (self.memberid), level="debug")
      p = {}
      for f in self.fields:
        p[f] = getattr(self, f)

      ttyio.echo("Player.save.100: p=%r" % (p), level="debug")

      dbh = bbsengine.databaseconnect(self.args)
      ttyio.echo("Player.save.140: trying update")
      res = bbsengine.update(dbh, "murdermotel.player", self.name, p, primarykey="name", mogrify=True)
      ttyio.echo("Player.save.120: res=%r" % (res), level="debug")
      if res is None:
        ttyio.echo("Player.save.160: update failed, trying insert")
        ttyio.echo("Player.save.180: p=%r" % (p), level="debug")
        bbsengine.insert(dbh, "murdermotel.player", p, primarykey="name", returnid=False, mogrify=True)
      self.isdirty = False
      dbh.commit()
      return True

def setarea(args, player, left):
    def right():
        debug = True if args is not None and args.debug is True else False

        buf = "murder motel"
        if player is not None:
          if player.isdirty is True:
              isdirty = "*"
          else:
              isdirty = ""

          debug = " | debug" if args is not None and args.debug is True else ""

          turn = " | %s" % (bbsengine.pluralize(4-player.turn, "turn remains", "turns remain"))

          if player.roomid is not None:
            room = " | room #%d" % (player.roomid)
            currentroom = getroom(args, player.roomid)
            if currentroom is not None and currentroom.shortname is not None:
              room += " "+currentroom.shortname
          else:
            room = ""

          moves = " | %s" % (bbsengine.pluralize(player.moves, "move remains", "moves remain"))

          buf += " | %s%s%s%s%s%s" % (isdirty, player.name, room, turn, moves, debug)

        if debug is True:
            buf += "| debug"

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
  x = "%s.%s" % (PACKAGENAME, submodule)
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
