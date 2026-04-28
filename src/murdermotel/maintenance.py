from bbsengine6 import database, io

from . import room as libroom, item as libitem


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

    step = 0

    screen.updateprogress(step, total)

    with database.cursor(conn) as cur:
        q = database.query("SELECT COUNT(*) AS count FROM $murdermotel.item")
        cur.execute(q)
        if cur.rowcount == 0:
            count = 0
        else:
            row = cur.fetchone()
            count = row["count"]

    screen.updateprogress(step, total)
    step += 1

    if count > 0:
        if (
            io.inputboolean(
                "{var:promptcolor}redistribute weapons, defenses, and specials? [yN]: {var:inputcolor}",
                "N",
                **kwargs,
            )
            is False
        ):
            return False

    with database.cursor(conn) as cur:
        q = database.query("DELETE FROM $murdermotel.item")
        cur.execute(q)
        screen.updateprogress(step, total)
        step += 1

        q = database.query("DELETE FROM $murdermotel.map_item_player")
        cur.execute(q)
        screen.updateprogress(step, total)
        step += 1

        q = database.query("DELETE FROM $murdermotel.map_item_room")
        cur.execute(q)
        screen.updateprogress(step, total)
        step += 1

    for name, data in items.items():
        i = libitem.Item(args)
        i.name = name
        i.type = data["kind"]
        i.title = data["title"]
        i.usemessages = data["usemessages"] if "usemessages" in data else []
        i.save(conn=conn)

        step += 1
        screen.updateprogress(step, total)

    step += 1

    boobytrap_item = {
        "name": "boobytrap",
        "serial": 1,
        "kind": "boobytrap",
        "modulepath": "boobytrap",
        "title": "Booby Trap",
    }
    if not database.upsert(
        args,
        "murdermotel.item",
        boobytrap_item,
        conflict_columns=["name", "serial"],
        update_columns=["kind", "modulepath", "title"],
        mogrify=False,
        conn=conn,
    ):
        io.echo(
            "mm.maintenance._populate_items.105: boobytrap item upsert failed",
            level="error",
        )
        return False
    screen.updateprogress(step, total)
    step += 1

    for x in range(0, 6):
        for name, data in items.items():
            m = {}
            m["roomid"] = random.randint(10, kk - 10)
            m["itemname"] = name
            m["serial"] = x + 1

            if not database.insert(
                args,
                "murdermotel.map_item_room",
                m,
                mogrify=False,
                returnid=False,
                conn=conn,
            ):
                io.echo(
                    "mm.maintenance._populate_items.110: insert failed", level="error"
                )
                return False

    screen.updateprogress(step, total)
    step += 1

    conn.commit()
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
            **kwargs,
        )
        is True
    ):
        playground(args, **kwargs)
    if (
        io.inputboolean(
            "{var:promptcolor}create weapons? {var:optioncolor}[{var:currentoptioncolor}Y{var:optioncolor}n]{var:promptcolor}: {var:inputcolor}",
            "Y",
            **kwargs,
        )
        is True
    ):
        weapons(args, **kwargs)
