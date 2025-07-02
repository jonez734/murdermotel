from bbsengine6 import io, member, database
from . import lib as libmm, room as libroom, item as libitem

def init(args, **kwargs):
    return True

def access(args, op, **kwargs):
    return True

def buildargs(args, **kwargs):
    return None

def main(args, **kwargs):
    def _work(conn):
        # io.echo(f"mm.startup.main._work.100: {conn=}", level="debug")

        def _items(args, **kwargs):
            ITEMS = {
                "axeblade" :      {"title":"axe blade",       "usemessages":["You swing the axe with all your might and slaughter", "THUCK! WHACK! THUCK! You hack away and finish", "You butcher"], "type":"component"},
                "pistol"   :      {"title":"pistol",          "usemessages":["You take aim.. pull the trigger.. and waste", "BANG! BANG! You gun down the vermin called", "You take aim and shoot"], "type":"component"},
                "chlorinegas" :   {"title":"chlorine gas",    "usemessages":["The noxious fumes spread from the sprayer and poison","The chlorine spews out and asphyxiates your mortal enemy", "You gas"], "type":"component"},
                "flamethrower" :  {"title":"flame thrower",   "usemessages":["You barbecue", "You pull out your flame thrower and fry", "Heat and light burst from the flame gun as you cook"], "type":"component"},
                "industrialacid": {"title":"industrial acid", "usemessages":["You boil away","You pump the acid sprayer furiously and disolve", "The acid hisses from the nozzle of your sprayer. It liquifies"], "type":"component"},

                "axehandle" :     {"title":"axe handle", "type":"component"},
                "bullets":        {"title":"bullets", "type":"component"},
                "gassprayer":     {"title":"gas sprayer", "type":"component"},
                "lighterfluid":   {"title":"lighter fluid", "type":"component"},
                "acidsprayer":    {"title":"acid sprayer", "type":"component"},

                "riotshield":       {"title":"riot shield", "type":"defense"},
                "flakjacket":       {"title":"flak jacket", "type":"defense"},
                "gasmask":          {"title":"gas mask", "type":"defense"},
                "fireextinguisher": {"title":"fire extinguisher", "type":"defense"},
                "lye":              {"title":"lye", "type":"defense"},

                "boobytrap":        {"title":"booby trap", "type":"boobytrap", "module":"boobytrap"},
            }
            
            if libitem.getcount(args, conn=conn) > 0:
                io.echo("SKIP", level="warn")
                return True

            for name, data in ITEMS.items():
                rec = {}
                rec["type"] = data.get("type", "item")
                rec["name"] = name
                rec["title"] = data.get("title", name)
                rec["type"] = data.get("type", None)
                rec["module"] = data.get("module", None)
                rec["state"] = database.Jsonb({"usemessages": data.get("usemessages", None)})
                database.insert(args, f"{libmm.SCHEMA}.item", rec, conn=conn, primarykey="name")
        
        def _classes(args, **kwargs):
            classlist = (
                (f"{libmm.SCHEMA}.player", "player.sql"),
                (f"{libmm.SCHEMA}.playground", "playground.sql"),
                (f"{libmm.SCHEMA}.item", "item.sql"),
                (f"{libmm.SCHEMA}.npc", "npc.sql"),
            )

            failcount = 0
            for (name, sqlfile) in classlist:
                io.echo(f"{{var:labelcolor}}class {{var:valuecolor}}{name}{{var:labelcolor}}: ", end="")
                if database.classexists(args, name, conn=conn) is False:
                    io.echo("import ", end="")
                    if database.importsql(args, sqlfile, conn=conn, package="murdermotel.data.sql") is False:
                        failcount += 1
                    else:
                        io.echo(" ok ", level="ok")
                else:
                    io.echo("ok", level="ok")
        
        def npccount(args, **kwargs):
            def _work(conn):
                with database.cursor(conn) as cur:
                    sql = f"select count(*) from {libmm.SCHEMA}.npc"
                    cur.execute(sql)
                    if cur.rowcount == 0:
                        return 0
                    return cur.fetchone()["count"]
            
            conn = kwargs.get("conn", None)
            if conn is None:
                pool = kwargs.get("pool", None)
                if pool is None:
                    io.echo(f"mm.startup.npccount.100: {pool=}", level="error")
                    return False
                with database.connect(args, pool=pool) as conn:
                    return _work(conn)
            return _work(conn)

        def _npcs(args, **kwargs):
            return True

        def _rooms(args, **kwargs):
            import re
            io.echo(f"mm.startup._rooms: {kwargs=}", level="debug")

            x = re.compile(r"(?:[\s]+)?data(\")?(?P<title>[\w\s'\(\)/#!.{}-]+)(\")?,(?P<east>\d{,3}),(?P<north>\d{,3}),(?P<west>\d{,3}),(?P<south>\d{,3}),(?P<up>\d{,3}),(?P<down>\d{,3})")
            def _work(conn):
                from . import data
                with data.get("playground.txt") as p:
                    io.echo(f"mm.startup._rooms.120: {p=}", level="debug")
                    roomid = 1
                    for line in p:
                        io.echo(f"mm.startup._rooms.100: {line=}", level="debug")
                        r = x.match(line)
                        if r is not None:
                            room = {}
                            room["id"] = roomid
                            room["title"] = r.group("title").lower()
                            for exit in ("north", "south", "east", "west", "up", "down"):
                                rn = int(r.group(exit))
                                if rn == 0:
                                    rn = None
                                room[exit] = rn
                            io.echo(f"{room=}", level="debug")

                            res = database.insert(args, "murdermotel.playground", room, primarykey="id", conn=conn)
                            io.echo(f"{res=}", level="debug")
                            roomid += 1
                        else:
                            io.echo(f"no match: {line} ({roomid})", level="debug")
                return True
            conn = kwargs.get("conn", None)
            if conn is None:
                pool = kwargs.get("pool", None)
                if pool is None:
                    io.echo(f"mm.startup.npccount.100: {pool=}", level="error")
                    return False
                with database.connect(args, pool=pool) as conn:
                    return _work(conn)
            return _work(conn)

        io.echo(f"{{var:labelcolor}}schema {{var:valuecolor}}{libmm.SCHEMA}: ", end="")
        if database.schemaexists(args, libmm.SCHEMA, conn=conn, **kwargs) is False:
            if database.createschema(args, libmm.SCHEMA, conn=conn, **kwargs) is False:
                io.echo(f"fail", level="error")
                return False
        io.echo(" ok ", level="ok")

        failcount = 0
        if _classes(args, conn=conn) is False:
            return False

        io.echo(f"{{var:labelcolor}}schema {{var:valuecolor}}murdermotel {{var:labelcolor}}privs: ", end="")
        for r in ("web", "term", "sysop"):
            if database.manage_schema_priv(args, "grant", "usage", libmm.SCHEMA, r, conn=conn, **kwargs) is False:
                io.echo(f"fail", level="error")
                failcount += 1
            else:
                io.echo(f" ok ", level="ok")

        io.echo(f"{{var:labelcolor}}schema {{var:valuecolor}}{libmm.SCHEMA} {{var:labelcolor}}create priv for sysop: ", end="")
        if database.manage_schema_priv(args, "grant", "create", libmm.SCHEMA, "sysop", conn=conn, **kwargs) is False:
            io.echo(f"fail", level="error")
            failcount += 1
        else:
            io.echo(f" ok ", level="ok")
        
        if failcount > 0:
            io.echo("fail", level="error")
            return False

        io.echo(f"{{var:labelcolor}}populate {{var:valuecolor}}rooms: ", end="")
        if libroom.getcount(args, conn=conn) == 0:
            if _rooms(args, conn=conn) is False:
                failcount += 1
                io.echo(f"fail", level="error")
            else:
                io.echo(f" ok ", level="ok")
        else:
            io.echo("skip", level="info")

        io.echo(f"{{var:labelcolor}}populate {{var:valuecolor}}items: ", end="")
        if libmm.getitemcount(args, conn=conn) == 0:
            if _items(args, **kwargs) is False:
                failcount += 1
                io.echo(f"fail", level="error")
            else:
                io.echo(f" ok ", level="ok")
        else:
            io.echo("skip", level="ok")
        
        io.echo(f"{{var:labelcolor}}populate {{var:valuecolor}}NPCs: ", end="")
        if libmm.getnpccount(args, conn=conn) == 0:
            if _npcs(args, **kwargs) is False:
                failcount += 1
                io.echo(f"fail", level="error")
            else:
                io.echo(f" ok ", level="ok")
        else:
            io.echo("skip", level="ok")
        
        if failcount > 0:
            io.echo(f" startup failed ", level="error")
            return False
        conn.commit()
        return True
        
    conn = kwargs.get("conn", None)
    io.echo(f"{conn=}", level="debug")
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo(f"{libmm.SCHEMA}.startup.100: {pool=}", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)
