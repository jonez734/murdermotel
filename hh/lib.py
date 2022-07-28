import ttyio5 as ttyio
import bbsengine5 as bbsengine

currentplayer = None
def setcurrentplayer(player):
  global currentplayer
  currentplayer = player

def getcurrentplayer():
  global currentplayer
  return currentplayer

def setarea(args, player, left):
    def right():
        debug = True if args is not None and args.debug is True else False

        if player is not None:
            if player.isdirty is True:
                isdirty = "*"
            else:
                isdirty = ""
            debug = " | debug" if args is not None and args.debug is True else ""

            turn = " | %s" % (bbsengine.pluralize(4-player.turn, "turn remains", "turns remain"))

            return "homicide hotel | %s%s%s%s" % (isdirty, player.name, turn, debug)
        else:
            if debug is True:
                return "debug"
            else:
                return ""
    bbsengine.setarea(left, right)
    return

def init(args=None):
  ttyio.setvariable("optioncolor", "{white}{bggray}")
  ttyio.setvariable("menudesc", "{/bgcolor}{white}")
  ttyio.setvariable("valuecolor", "{/bgcolor}{green}")
  ttyio.setvariable("promptcolor", "{/bgcolor}{lightgray}")
  ttyio.setvariable("inputcolor", "{/bgcolor}{green}")
