import argparse
import random

import ttyio5 as ttyio
import bbsengine5 as bbsengine

def init(args=None):
  ttyio.setvariable("menuoption", "{white}{bggray}")
  ttyio.setvariable("menudesc", "{/bgcolor}{white}")
  ttyio.setvariable("menuvalue", "{/bgcolor}{green}")
  ttyio.setvariable("promptcolor", "{/bgcolor}{lightgray}")
  ttyio.setvariable("inputcolor", "{/bgcolor}{green}")
  return

def setarea(args, left, dirty=False):
  def right():
    currentmember = bbsengine.getcurrentmember(args)
    if currentmember is None:
      return ""
    rightbuf = "| %s | %s" % (currentmember["name"], bbsengine.pluralize(currentmember["credits"], "credit", "credits"))
    if args.debug is True:
      rightbuf += " | debug"
    if dirty is True:
      rightbuf += " | dirty"
    return rightbuf
  bbsengine.setarea(left, right)

def weapons(args):
  kk = 140
  for t in range(0, 90+1):
    ttyio.echo("t=%r" % (t))
    ttyio.echo("randint=%r" % (random.randint(10, kk-10)))

def main(args):
    if args is not None and "debug" in args and args.debug is True:
        ttyio.echo("hotelsetup.main.100: args=%r" % (args))

#    ch = ttyio.inputboolean("create playground? [Yn]: ", "Y")
#    ch = ttyio.inputboolean("create players? [Yn]: ", "Y")
    if ttyio.inputboolean("create weapons? [Yn]: ", "Y") is True:
      weapons(args)
