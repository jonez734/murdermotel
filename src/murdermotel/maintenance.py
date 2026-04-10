# import ttyio5 as ttyio
# import bbsengine5 as bbsengine
from bbsengine6 import database, io

from . import lib, room as libroom


def init(args=None, **kw):
    #  ttyio.setvariable("menuoption", "{white}{bggray}")
    #  ttyio.setvariable("menudesc", "{/bgcolor}{white}")
    #  ttyio.setvariable("menuvalue", "{/bgcolor}{green}")
    #  ttyio.setvariable("promptcolor", "{/bgcolor}{lightgray}")
    #  ttyio.setvariable("inputcolor", "{/bgcolor}{green}")
    return True


#
# r"(?P<whitspace>[\s]+)?data(\")?(?P<name>[\w\s']+)(\")?,(?P<east>\d{,3}),(?P<north>\d{,3}),(?P<west>\d{,3}),(?P<south>\d{,3}),(?P<up>\d{,3}),(?P<down>\d{,3})"g
#


def access(args, op, **kwargs):
    return True


def buildargs(args=None, **kwargs):
    return None


def weapons(args, items=None, **kwargs):
    kk = libroom.getcount(args, **kwargs)
    if kk == 0:
        io.echo("playground has not been created", level="error")
        return False

    if items is None:
        io.echo("no items to distribute", level="error")
        return False

    io.echo("reticulating splines...")
    total = len(items) * 6

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"mm.maint.200: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _weapons_work(args, conn, items, kk, total, **kwargs)
    return _weapons_work(args, conn, items, kk, total, **kwargs)


def _weapons_work(args, conn, items, kk, total, **kwargs):
    import random
    from bbsengine6 import screen

    dbh = database.connect(args)

    step = 0

    screen.updateprogress(step, total)

    sql = "select count(name) from murdermotel.item"
    cur = dbh.cursor()
    cur.execute(sql)

    screen.updateprogress(step, total)
    step += 1

    if cur.rowcount > 0:
        if (
            io.inputboolean(
                "{var:promptcolor}redistribute weapons, defenses, and specials? [yN]: {var:inputcolor}",
                "N",
            )
            is False
        ):
            return False

    sql = "delete from murdermotel.item"
    cur.execute(sql)
    screen.updateprogress(step, total)
    step += 1

    sql = "delete from murdermotel.map_item_player"
    cur.execute(sql)
    screen.updateprogress(step, total)
    step += 1

    sql = "delete from murdermotel.map_item_room"
    cur.execute(sql)
    screen.updateprogress(step, total)
    step += 1

    for name, data in items.items():
        i = lib.Item(args)
        i.name = name
        i.type = data["type"]
        i.title = data["title"]
        i.usemessages = data["usemessages"] if "usemessages" in data else []
        i.save()

        step += 1
        screen.updateprogress(step, total)

    step += 1

    for x in range(0, 6):
        for name in items.keys():
            map = {}
            map["roomid"] = random.randint(10, kk - 10)
            map["itemname"] = name

            database.insert(
                args, "murdermotel.map_item_room", map, mogrify=True, returnid=False
            )

    screen.updateprogress(step, total)
    step += 1

    #  for x in range(0, 90+1):
    #    roomid = random.randint(10, kk-10)
    #    i = lib.Item(args)
    #    ttyio.echo("t=%r" % (t))
    #    ttyio.echo("randint=%r" % (random.randint(10, kk-10)))
    dbh.commit()
    #  bbsengine.updateprogress(total, total)
    io.echo("OK.{f6}reticulation of splines completed")
    io.echo("{var:promptcolor}press any key: ", end="", flush=True)
    io.getch()


def playground(args, **kwargs):
    io.echo("playground creation not yet implemented")
    return False


def main(args, **kwargs):
    if args is not None and "debug" in args and args.debug is True:
        io.echo(f"mm.maint.main.100: {args=}", level="debug")

    if (
        io.inputboolean(
            "{var:promptcolor}create playground? {var:optioncolor}[{var:currentoptioncolor}Y{var:optioncolor}n]{var:promptcolor}]: {var:inputcolor}",
            "Y",
        )
        is True
    ):
        playground(args, **kwargs)
    if (
        io.inputboolean(
            "{var:promptcolor}create weapons? {var:optioncolor}[{var:currentoptioncolor}Y{var:optioncolor}n]{var:promptcolor}: {var:inputcolor}",
            "Y",
        )
        is True
    ):
        weapons(args, **kwargs)
