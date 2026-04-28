# obj.py
# Base object classes and registry for murdermotel game objects

from __future__ import annotations

from typing import Optional

from bbsengine6 import database, io


class ObjectRegistry:
    """Registry for active game objects (NPCs, items) that need turn processing."""

    def __init__(self):
        self._objects: list = []

    def register(self, obj) -> None:
        if obj not in self._objects:
            self._objects.append(obj)

    def unregister(self, obj) -> None:
        if obj in self._objects:
            self._objects.remove(obj)

    def get_by_room(self, roomid: int) -> list:
        return [obj for obj in self._objects if obj.roomid == roomid]

    def all(self) -> list:
        return list(self._objects)

    def clear(self) -> None:
        self._objects.clear()

    def get_by_name(self, name: str):
        for obj in self._objects:
            if getattr(obj, "name", None) == name:
                return obj
        return None


registry = ObjectRegistry()


class Obj(object):
    modulepath = None

    def __init__(self, args):
        self.args = args
        self.table = "murdermotel.player"
        self.fields = ()
        self.classname = self.__class__.__name__
        self.name = None

    def on_turn(self, args, room=None, **kwargs) -> Optional[bool]:
        from . import lib as libmm

        if self.modulepath:
            return libmm.runmodule(
                args, "turn", self.modulepath, obj=self, room=room, **kwargs
            )
        return True

    def short(self) -> str:
        return f"{self.classname}"

    def load(self, name, **kwargs) -> bool:
        def _work(conn):
            if self.args.debug is True:
                io.echo(f"{name}.load({self.classname})", level="debug")
            with database.cursor(conn) as cur:
                q = database.query(
                    "SELECT * FROM $murdermotel.player WHERE moniker = :name", name=name
                )
                cur.execute(q)
                if cur.rowcount == 0:
                    io.echo(f"unable to load record {name!r}", level="error")
                    return False
                rec = cur.fetchone()
                for f in self.fields:
                    setattr(self, f, rec[f])
            return True

        conn = kwargs.get("conn", None)
        if conn is None:
            pool = kwargs.get("pool", None)
            if pool is None:
                io.echo(f"{self.classname}.load.100: pool is None", level="error")
                return False
            with database.connect(self.args, pool=pool) as conn:
                return _work(conn)
        return _work(conn)

    def save(self, **kwargs) -> bool:
        def _work(conn):
            p = {}
            for f in self.fields:
                p[f] = getattr(self, f)
            io.echo(f"{self.classname}.save.100: p={p!r}", level="debug")

            if self.args.debug is True:
                io.echo(f"{self.classname}.save.120: trying update", level="debug")
            res = database.update(
                self.args,
                self.table,
                self.name,  # type: ignore[arg-type]
                p,
                primarykey="moniker",
                mogrify=False,
                conn=conn,
            )
            if self.args.debug is True:
                io.echo(f"{self.classname}.save.140: res={res!r}", level="debug")
            if res == 0:
                if self.args.debug is True:
                    io.echo(
                        f"{self.classname}.save.160: update failed, trying insert. p={p!r}",
                        level="debug",
                    )
                if not database.insert(
                    self.args,
                    self.table,
                    p,
                    primarykey="name",
                    returnid=False,
                    mogrify=False,
                    conn=conn,
                ):
                    io.echo(f"{self.classname}.save.170: insert failed", level="error")
                    return False
            return True

        conn = kwargs.get("conn", None)
        if conn is None:
            pool = kwargs.get("pool", None)
            if pool is None:
                io.echo(f"{self.classname}.save.100: pool is None", level="error")
                return False
            with database.connect(self.args, pool=pool) as conn:
                _work(conn)
        else:
            _work(conn)
        self.isdirty = False
        return True

    def move(self, args, roomid: int, **kwargs) -> bool:
        """Move object to specified room id.

        Args:
            args: command-line args
            roomid: target room ID to move to

        Returns:
            True if move successful, False otherwise
        """
        from . import room as libroom

        if not libroom.is_valid(args, roomid, **kwargs):
            io.echo(f"Obj.move.100: invalid roomid {roomid}", level="debug")
            return False
        self.roomid = roomid
        return True


class Living(Obj):
    def __init__(self, args):
        super().__init__(args)
        self.roomid = None

    def short(self) -> str:
        return "NEEDINFO.living"
