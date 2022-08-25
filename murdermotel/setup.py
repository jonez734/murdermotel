import re
import json
import random

import ttyio5 as ttyio
import bbsengine5 as bbsengine

from . import lib
from . import data

def init(args=None, **kw):
#  ttyio.setvariable("menuoption", "{white}{bggray}")
#  ttyio.setvariable("menudesc", "{/bgcolor}{white}")
#  ttyio.setvariable("menuvalue", "{/bgcolor}{green}")
#  ttyio.setvariable("promptcolor", "{/bgcolor}{lightgray}")
#  ttyio.setvariable("inputcolor", "{/bgcolor}{green}")
  return

#
# r"(?P<whitspace>[\s]+)?data(\")?(?P<name>[\w\s']+)(\")?,(?P<east>\d{,3}),(?P<north>\d{,3}),(?P<west>\d{,3}),(?P<south>\d{,3}),(?P<up>\d{,3}),(?P<down>\d{,3})"g
#

def weapons(args):
  kk = 140
  for t in range(0, 90+1):
    ttyio.echo("t=%r" % (t))
    ttyio.echo("randint=%r" % (random.randint(10, kk-10)))

def playground(args):
  x = re.compile(r"(?P<whitespace>[\s]+)?data(\")?(?P<name>[\w\s'\(\)/#!.{}-]+)(\")?,(?P<east>\d{,3}),(?P<north>\d{,3}),(?P<west>\d{,3}),(?P<south>\d{,3}),(?P<up>\d{,3}),(?P<down>\d{,3})")
  def process(f):
    roomid = 1
    for line in f:
      r = x.match(line)
      if r is not None:
        room = {}
        room["id"] = roomid
        room["name"] = r.group("name").lower()
        for exit in ("north", "south", "east", "west", "up", "down"):
          room[exit] = int(r.group(exit))
        print(room)
        roomid += 1
      else:
        ttyio.echo("no match: %r (roomid=%s)" % (line, roomid), level="debug")
  filename = data.get("playground.txt")
  ttyio.echo("playground.100: filename=%r type=%r" % (filename, type(filename)), level="debug")
  if type(filename) == str:
    with open(filename) as f:
      process(f)
  else:
    with filename as f:
      process(f)

def main(args, **kw):
    if args is not None and "debug" in args and args.debug is True:
        ttyio.echo("hotelsetup.main.100: args=%r" % (args), level="debug")

#    ch = ttyio.inputboolean("create playground? [Yn]: ", "Y")
#    ch = ttyio.inputboolean("create players? [Yn]: ", "Y")
    if ttyio.inputboolean("{var:promptcolor}create weapons? {var:optioncolor}[{var:currentoptioncolor}Y{var:optioncolor}n]{var:promptcolor}: {var:inputcolor}", "Y") is True:
      weapons(args)
    if ttyio.inputboolean("{var:promptcolor}create playground? {var:optioncolor}[{var:currentoptioncolor}Y{var:optioncolor}n]{var:promptcolor}]: {var:inputcolor}", "Y") is True:
      playground(args)
