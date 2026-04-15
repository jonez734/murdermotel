# startup.py
# Initialises the murdermotel schema, tables, privileges, and seed data.

import re

from bbsengine6 import database, io

from . import lib as libmm, room as libroom

_SQL_PACKAGE = "murdermotel.data.sql"

_ROOM_MODULEPATHS = {
    128: "inside_glowing_sphere",
}

# Tables to create, in dependency order.
_TABLES = (
    (f"{libmm.SCHEMA}.player", "player.sql"),
    (f"{libmm.SCHEMA}.playground", "playground.sql"),
    (f"{libmm.SCHEMA}.item", "item.sql"),
    (f"{libmm.SCHEMA}.npc", "npc.sql"),
    (f"{libmm.SCHEMA}.defense", "defense.sql"),
    (f"{libmm.SCHEMA}.weapon", "weapon.sql"),
    (f"{libmm.SCHEMA}.boobytrap", "boobytrap.sql"),
    (f"{libmm.SCHEMA}.thief", "thief.sql"),
    (f"{libmm.SCHEMA}.rabidwolf", "rabidwolf.sql"),
)

# Roles granted USAGE on the schema.
_USAGE_ROLES = ("web", "term", "sysop")

# Regex for parsing playground.txt room lines.
_ROOM_RE = re.compile(
    r"(?:[\s]+)?data(\")?(?P<title>[\w\s'\(\)/#!.{}-]+)(\")?"
    r",(?P<east>\d{,3}),(?P<north>\d{,3}),(?P<west>\d{,3})"
    r",(?P<south>\d{,3}),(?P<up>\d{,3}),(?P<down>\d{,3})"
)


def init(args, **kwargs) -> bool:
    return True


def access(args, op, **kwargs) -> bool:
    return True


def buildargs(args, **kwargs):
    return None


def main(args, **kwargs) -> bool:
    def _work(conn):
        io.echo("running startup...")

        # --- schema ---
        io.echo(f"{{var:labelcolor}}schema {{var:valuecolor}}{libmm.SCHEMA}: ", end="")
        if not database.schemaexists(args, libmm.SCHEMA, conn=conn):
            if not database.createschema(args, libmm.SCHEMA, conn=conn):
                io.echo("fail", level="error")
                return False
        io.echo(" ok ", level="ok")

        # --- tables ---
        failcount = 0
        for table, sqlfile in _TABLES:
            io.echo(
                f"{{var:labelcolor}}table {{var:valuecolor}}{table}{{var:labelcolor}}: ",
                end="",
            )
            if not database.classexists(args, table, conn=conn):
                io.echo("import ", end="")
                if not database.importsql(
                    args, sqlfile, conn=conn, package=_SQL_PACKAGE
                ):
                    io.echo("fail", level="error")
                    failcount += 1
                else:
                    io.echo(" ok ", level="ok")
            else:
                io.echo("ok", level="ok")

        if failcount > 0:
            io.echo("table setup failed", level="error")
            conn.rollback()
            return False

        # --- schema privileges ---
        io.echo(
            f"{{var:labelcolor}}schema {{var:valuecolor}}{libmm.SCHEMA} "
            f"{{var:labelcolor}}privs: ",
            end="",
        )
        for role in _USAGE_ROLES:
            if not database.manage_schema_priv(
                args, "grant", "usage", libmm.SCHEMA, role, conn=conn
            ):
                io.echo(f"fail ({role})", level="error")
                failcount += 1

        if not database.manage_schema_priv(
            args, "grant", "create", libmm.SCHEMA, "sysop", conn=conn
        ):
            io.echo("fail (sysop create)", level="error")
            failcount += 1

        if failcount > 0:
            io.echo("privilege setup failed", level="error")
            conn.rollback()
            return False

        io.echo(" ok ", level="ok")

        # --- rooms ---
        io.echo("{var:labelcolor}populate {var:valuecolor}rooms: ", end="")
        if (libroom.getcount(args, conn=conn) or 0) == 0:
            if not _populate_rooms(args, conn=conn):
                io.echo("fail", level="error")
                failcount += 1
            else:
                io.echo(" ok ", level="ok")
        else:
            io.echo("skip", level="info")

        # --- items ---
        io.echo("{var:labelcolor}populate {var:valuecolor}items: ", end="")
        if (libmm.getitemcount(args, conn=conn) or 0) == 0:
            if not database.importsql(
                args, "items.sql", conn=conn, package=_SQL_PACKAGE
            ):
                io.echo("fail", level="error")
                failcount += 1
            else:
                io.echo(" ok ", level="ok")
        else:
            io.echo("skip", level="ok")

        # --- distribute items ---
        io.echo("{var:labelcolor}distribute {var:valuecolor}items: ", end="")
        if (libmm.countdistributeditems(args, conn=conn) or 0) > 0:
            io.echo("skip", level="ok")
        else:
            if libmm.distributeitems(args, conn=conn):
                io.echo(" ok ", level="ok")
            else:
                io.echo("fail", level="error")
                failcount += 1

        # --- NPCs ---
        io.echo("{var:labelcolor}populate {var:valuecolor}NPCs: ", end="")
        if (libmm.getnpccount(args, conn=conn) or 0) == 0:
            if not database.importsql(
                args, "npcs.sql", conn=conn, package=_SQL_PACKAGE
            ):
                io.echo("fail", level="error")
                failcount += 1
            else:
                io.echo(" ok ", level="ok")
        else:
            io.echo("skip", level="ok")

        if failcount > 0:
            io.echo("startup failed", level="error")
            conn.rollback()
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


def _populate_rooms(args, **kwargs) -> bool:
    """Parse playground.txt and insert rooms into the database."""

    def _work(conn):
        from . import data

        with data.get("playground.txt") as p:
            roomid = 1
            for line in p:
                io.echo(f"mm.startup._populate_rooms: {line=}", level="debug")
                m = _ROOM_RE.match(line)
                if m is None:
                    io.echo(f"no match: {line!r} (roomid={roomid})", level="debug")
                    continue

                if roomid in _ROOM_MODULEPATHS:
                    modulepath = _ROOM_MODULEPATHS[roomid]
                else:
                    modulepath = None
                room = {"id": roomid, "title": m.group("title").lower(), "modulepath":modulepath}
                for direction in ("north", "south", "east", "west", "up", "down"):
                    val = int(m.group(direction))
                    if val == 150:
                        room[direction] = roomid
                    else:
                        room[direction] = val if val != 0 else None
                io.echo(f"{room=}", level="debug")
                database.insert(
                    args,
                    f"{libmm.SCHEMA}.playground",
                    room,
                    primarykey="id",
                    conn=conn,
                    commit=True,
                )
                roomid += 1
        return True

    conn = kwargs.get("conn", None)
    if conn is None:
        pool = kwargs.get("pool", None)
        if pool is None:
            io.echo("mm.startup._populate_rooms.100: no pool", level="error")
            return False
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)
