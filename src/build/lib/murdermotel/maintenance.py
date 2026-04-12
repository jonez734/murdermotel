import re
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


def access(args, op, **kw):
    return True


def weapons(args):
    # \c8axe handle\cl
    # \c8pistol\cl
    # \c8chlorine gas\cl
    # \c8flame thrower\cl
    # \c8industrial acid\cl

    # \c8axe blade\cl
    # \c8bullets\cl
    # \c8gas sprayer\cl
    # \c8lighter fluid\cl
    # \c8acid sprayer\cl

    # \c3riot shield\cl
    # \c3flak jacket\cl
    # \c3gas mask\cl
    # \c3fire extinguisher\cl
    # \c3lye\cl

    # [x] You butcher
    # [x] You take aim & shoot
    # [x] You gas
    # [x] You pull out your fueled flame throwerand fry
    # [x] You pump the acid sprayer furiously and dissolve

    # [x] You swing the axe with all your mightand slaughter
    # [x] You take aim.. Pull the trigger.. And waste
    # [x] The noxious fumes spread from the sprayer and poison
    # [x] Heat and light burst from the flame gun as you cook
    # [x] The acid hisses from the nossle of your sprayer. It liquifies

    # [x] THUCK! WHACK! THUCK! You hack awayand finish
    # [x] BANG\b1 BANG\b1!!! You gun down the vermincalled
    # [x] The chlorine spews out ans asphyxiates your mortal enemy
    # [x] You barbecue
    # [x] You boil away

    items = {
        "axeblade": {
            "title": "axe blade",
            "usemessages": [
                "You swing the axe with all your might and slaughter",
                "THUCK! WHACK! THUCK! You hack away and finish",
                "You butcher",
            ],
            "type": "component",
        },
        "pistol": {
            "title": "pistol",
            "usemessages": [
                "You take aim.. pull the trigger.. and waste",
                "BANG! BANG! You gun down the vermin called",
                "You take aim and shoot",
            ],
            "type": "component",
        },
        "chlorinegas": {
            "title": "chlorine gas",
            "usemessages": [
                "The noxious fumes spread from the sprayer and poison",
                "The chlorine spews out and asphyxiates your mortal enemy",
                "You gas",
            ],
            "type": "component",
        },
        "flamethrower": {
            "title": "flame thrower",
            "usemessages": [
                "You barbecue",
                "You pull out your flame thrower and fry",
                "Heat and light burst from the flame gun as you cook",
            ],
            "type": "component",
        },
        "industrialacid": {
            "title": "industrial acid",
            "usemessages": [
                "You boil away",
                "You pump the acid sprayer furiously and disolve",
                "The acid hisses from the nozzle of your sprayer. It liquifies",
            ],
            "type": "component",
        },
        "axehandle": {"title": "axe handle", "type": "component"},
        "bullets": {"title": "bullets", "type": "component"},
        "gassprayer": {"title": "gas sprayer", "type": "component"},
        "lighterfluid": {"title": "lighter fluid", "type": "component"},
        "acidsprayer": {"title": "acid sprayer", "type": "component"},
        "riotshield": {"title": "riot shield", "type": "defense"},
        "flakjacket": {"title": "flak jacket", "type": "defense"},
        "gasmask": {"title": "gas mask", "type": "defense"},
        "fireextinguisher": {"title": "fire extinguisher", "type": "defense"},
        "lye": {"title": "lye", "type": "defense"},
        "boobytrap": {"title": "booby trap", "type": "special"},
    }
    kk = lib.getroomcount(args)
    if kk == 0:
        ttyio.echo("playground has not been created", level="error")
        return False

    ttyio.echo("reticulating splines...")
    total = len(items) * 6

    dbh = bbsengine.databaseconnect(args)

    step = 0

    bbsengine.updateprogress(step, total)

    sql = "select count(name) from murdermotel.item"
    cur = dbh.cursor()
    cur.execute(sql)

    bbsengine.updateprogress(step, total)
    step += 1

    if cur.rowcount > 0:
        if (
            ttyio.inputboolean(
                "{var:promptcolor}redistribute weapons, defenses, and specials? [yN]: {var:inputcolor}",
                "N",
            )
            is False
        ):
            return False

    sql = "delete from murdermotel.item"
    cur.execute(sql)
    bbsengine.updateprogress(step, total)
    step += 1

    sql = "delete from murdermotel.map_item_player"
    cur.execute(sql)
    bbsengine.updateprogress(step, total)
    step += 1

    sql = "delete from murdermotel.map_item_room"
    cur.execute(sql)
    bbsengine.updateprogress(step, total)
    step += 1

    for name, data in items.items():
        i = lib.Item(args)
        i.name = name
        i.type = data["type"]
        i.title = data["title"]
        i.usemessages = data["usemessages"] if "usemessages" in data else []
        i.save()

        step += 1
        bbsengine.updateprogress(step, total)

    step += 1

    for x in range(0, 6):
        for name in items.keys():
            map = {}
            map["roomid"] = random.randint(10, kk - 10)
            map["itemname"] = name

            bbsengine.insert(
                dbh, "murdermotel.map_item_room", map, mogrify=True, returnid=False
            )

    bbsengine.updateprogress(step, total)
    step += 1

    #  for x in range(0, 90+1):
    #    roomid = random.randint(10, kk-10)
    #    i = lib.Item(args)
    #    ttyio.echo("t=%r" % (t))
    #    ttyio.echo("randint=%r" % (random.randint(10, kk-10)))
    dbh.commit()
    #  bbsengine.updateprogress(total, total)
    ttyio.echo("OK.{f6}reticulation of splines completed")
    ttyio.echo("{var:promptcolor}press any key: ", end="", flush=True)
    ttyio.getch()


def playground(args):
    playground = {}
    x = re.compile(
        r"(?:[\s]+)?data(\")?(?P<title>[\w\s'\(\)/#!.{}-]+)(\")?,(?P<east>\d{,3}),(?P<north>\d{,3}),(?P<west>\d{,3}),(?P<south>\d{,3}),(?P<up>\d{,3}),(?P<down>\d{,3})"
    )
    dbh = bbsengine.databaseconnect(args)

    def process(f):
        roomid = 1
        for line in f:
            r = x.match(line)
            if r is not None:
                room = {}
                room["roomid"] = roomid
                room["title"] = r.group("title").lower()
                for exit in ("north", "south", "east", "west", "up", "down"):
                    rn = int(r.group(exit))
                    if rn == 0:
                        rn = None
                    room[exit] = rn
                ttyio.echo("room=%r" % (room))

                res = bbsengine.insert(dbh, "murdermotel.playground", room, "roomid")
                ttyio.echo("res=%r" % (res), level="debug")
                roomid += 1
            else:
                ttyio.echo("no match: %r (roomid=%s)" % (line, roomid), level="debug")

    filename = data.get("playground.txt")
    # ttyio.echo("playground.100: filename=%r type=%r" % (filename, type(filename)), level="debug")
    with filename as f:
        process(f)
    dbh.commit()
    return


def main(args, **kw):
    if args is not None and "debug" in args and args.debug is True:
        ttyio.echo("mm.maint.main.100: args=%r" % (args), level="debug")

    if (
        ttyio.inputboolean(
            "{var:promptcolor}create playground? {var:optioncolor}[{var:currentoptioncolor}Y{var:optioncolor}n]{var:promptcolor}]: {var:inputcolor}",
            "Y",
        )
        is True
    ):
        playground(args)
    if (
        ttyio.inputboolean(
            "{var:promptcolor}create weapons? {var:optioncolor}[{var:currentoptioncolor}Y{var:optioncolor}n]{var:promptcolor}: {var:inputcolor}",
            "Y",
        )
        is True
    ):
        weapons(args)
