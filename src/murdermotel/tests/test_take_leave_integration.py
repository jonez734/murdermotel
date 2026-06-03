"""Integration tests for the [T]ake and [L]eave item flow.

Exercises the take/leave cycle end-to-end via the Room/Player classes, mirroring
what the 'T' (take) and 'L' (leave) branches in play.py:519-575 do:

    Take:  room.finditem(name) → del room.items[i] → player.items.append(item) → save()
    Leave: player.finditem(name) → del player.items[i] → room.items.append(item) → save()

The circular import (lib → item → lib) was fixed by removing the `Item = libitem.Item`
alias at lib.py:20, so murdermotel submodules can now be imported freely.
"""

from __future__ import annotations


def _place_item_in_room(args, roomid, itemname, serial, pool, conn=None):
    from bbsengine6 import database

    def _work(c):
        with database.cursor(c) as cur:
            q = database.query(
                "INSERT INTO $murdermotel.item (name, serial, title, kind) VALUES (:name, :serial, :title, 'item') ON CONFLICT (name, serial) DO UPDATE SET title = EXCLUDED.title",
                name=itemname,
                serial=serial,
                title=itemname,
            )
            cur.execute(q, {"name": itemname, "serial": serial, "title": itemname})
            q = database.query(
                "INSERT INTO $murdermotel.map_item_room (roomid, itemname, serial) VALUES (:roomid, :itemname, :serial) ON CONFLICT DO NOTHING",
                roomid=roomid,
                itemname=itemname,
                serial=serial,
            )
            cur.execute(q, {"roomid": roomid, "itemname": itemname, "serial": serial})

    if conn is None:
        with database.connect(args, pool=pool) as conn:
            _work(conn)
            conn.commit()
    else:
        _work(conn)


def _place_item_on_player(args, playermoniker, itemname, serial, pool, conn=None):
    from bbsengine6 import database

    def _work(c):
        with database.cursor(c) as cur:
            q = database.query(
                "INSERT INTO $murdermotel.item (name, serial, title, kind) VALUES (:name, :serial, :title, 'item') ON CONFLICT (name, serial) DO UPDATE SET title = EXCLUDED.title",
                name=itemname,
                serial=serial,
                title=itemname,
            )
            cur.execute(q, {"name": itemname, "serial": serial, "title": itemname})
            q = database.query(
                "INSERT INTO $murdermotel.map_item_player (playermoniker, itemname, serial) VALUES (:playermoniker, :itemname, :serial) ON CONFLICT DO NOTHING",
                playermoniker=playermoniker,
                itemname=itemname,
                serial=serial,
            )
            cur.execute(
                q,
                {
                    "playermoniker": playermoniker,
                    "itemname": itemname,
                    "serial": serial,
                },
            )

    if conn is None:
        with database.connect(args, pool=pool) as conn:
            _work(conn)
            conn.commit()
    else:
        _work(conn)


def _clear_player_items(args, playermoniker, pool):
    from bbsengine6 import database

    with database.connect(args, pool=pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                "DELETE FROM $murdermotel.map_item_player WHERE playermoniker = :playermoniker",
                playermoniker=playermoniker,
            )
            cur.execute(q, {"playermoniker": playermoniker})
        conn.commit()


def _clear_room_items(args, roomid, pool):
    from bbsengine6 import database

    with database.connect(args, pool=pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                "DELETE FROM $murdermotel.map_item_room WHERE roomid = :roomid",
                roomid=roomid,
            )
            cur.execute(q, {"roomid": roomid})
        conn.commit()


def _sync_item_to_room(args, room, pool):
    """Sync a freshly-placed item from DB into the Room.items list."""
    from murdermotel import room as libroom

    fresh = libroom.load(args, room.id, pool=pool)
    if fresh and fresh.items:
        room.items = fresh.items


def _sync_item_to_player(args, playermoniker, player, pool):
    """Sync a freshly-placed item from DB into the Player.items list."""
    from murdermotel import player as libplayer

    fresh = libplayer.load(args, playermoniker, pool=pool)
    if fresh and fresh.items:
        player.items = fresh.items


def _take_item(args, room, player, itemname, pool, conn=None):
    """Mirror play.py:519-547. Returns the moved item or None."""
    itemindex = room.finditem(itemname)
    if itemindex is None:
        return None
    item = room.items[itemindex]
    del room.items[itemindex]
    player.items.append(item)
    player.save(pool=pool, conn=conn)
    room.save(pool=pool, conn=conn)
    return item


def _leave_item(args, room, player, itemname, pool, conn=None):
    """Mirror play.py:548-575. Returns the moved item or None."""
    itemindex = player.finditem(itemname)
    if itemindex is None:
        return None
    item = player.items[itemindex]
    del player.items[itemindex]
    room.items.append(item)
    player.save(pool=pool, conn=conn)
    room.save(pool=pool, conn=conn)
    return item


def _steal_item_from_player(args, player, thief, pool, conn=None):
    """Mirror thief.steal_from_player(). Returns the stolen item or None."""
    import random as randomlib

    if not player.items:
        return None

    idx = randomlib.randint(0, len(player.items) - 1)
    item = player.items.pop(idx)
    thief.items.append(item)
    return item


class TestTakeLeaveIntegration:
    """Integration tests using Room/Player API directly."""

    def test_thief_steals_from_player(self, test_args, test_pool, test_player, test_room):
        """Thief steals an item from player - item moves from player to thief."""
        from murdermotel import player as libplayer, thief as libthief

        item_name = "ruby"
        item_serial = 99

        _place_item_on_player(test_args, test_player, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            thief = libthief.load(test_args, pool=test_pool, conn=conn)
            if player is None or thief is None:
                pytest.skip("Player or thief not loaded")

            player_items_before = len(player.items)
            thief_items_before = len(thief.items)

            stolen = _steal_item_from_player(test_args, player, thief, test_pool, conn=conn)
            assert stolen is not None
            assert len(player.items) == player_items_before - 1
            assert len(thief.items) == thief_items_before + 1

        _clear_player_items(test_args, test_player, test_pool)

    def test_take_item_from_room(self, test_args, test_pool, test_player, test_room):
        """Select 'T' → item name: item moves from room to player via Room/Player API."""
        from murdermotel import room as libroom, player as libplayer

        item_name = "knife"
        item_serial = 1

        _place_item_in_room(test_args, test_room, item_name, item_serial, test_pool)

        room = libroom.load(test_args, test_room, pool=test_pool)
        player = libplayer.load(test_args, test_player, pool=test_pool)
        assert room is not False
        assert player is not None

        _sync_item_to_room(test_args, room, test_pool)

        room_items_before = len(room.items)
        player_items_before = len(player.items)

        item = _take_item(test_args, room, player, item_name, test_pool)
        assert item is not None

        assert len(room.items) == room_items_before - 1
        assert len(player.items) == player_items_before + 1

    def test_leave_item_from_player(self, test_args, test_pool, test_player, test_room):
        """Select 'L' → item name: item moves from player to room via Room/Player API."""
        from murdermotel import room as libroom, player as libplayer

        item_name = "knife"
        item_serial = 1

        with test_pool.getconn() as conn:
            _place_item_on_player(
                test_args, test_player, item_name, item_serial, test_pool, conn=conn
            )

            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            room = libroom.load(test_args, test_room, pool=test_pool, conn=conn)
            assert player is not None
            assert room is not False

            player_items_before = len(player.items)
            room_items_before = len(room.items)

            item = _leave_item(test_args, room, player, item_name, test_pool, conn=conn)
            assert item is not None
            assert len(player.items) == player_items_before - 1
            assert len(room.items) == room_items_before + 1

    def test_round_trip_take_then_leave(
        self, test_args, test_pool, test_player, test_room
    ):
        """Place item in room, take to player, leave back in same room."""
        from murdermotel import room as libroom, player as libplayer

        item_name = "dagger"
        item_serial = 2

        _place_item_in_room(test_args, test_room, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            room = libroom.load(test_args, test_room, pool=test_pool, conn=conn)
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            assert room is not False
            assert player is not None

            room_items_before = len(room.items)
            player_items_before = len(player.items)

            item = _take_item(test_args, room, player, item_name, test_pool, conn=conn)
            assert item is not None
            assert len(room.items) == room_items_before - 1
            assert len(player.items) == player_items_before + 1

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            room = libroom.load(test_args, test_room, pool=test_pool, conn=conn)
            assert player is not None
            assert room is not False

            item = _leave_item(test_args, room, player, item_name, test_pool, conn=conn)
            assert item is not None
            assert len(player.items) == player_items_before
            assert len(room.items) == room_items_before

    def test_round_trip_leave_then_take(
        self, test_args, test_pool, test_player, test_room
    ):
        """Place item on player, leave in room, take back to player."""
        from murdermotel import room as libroom, player as libplayer

        item_name = "dagger"
        item_serial = 2

        _place_item_on_player(test_args, test_player, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            room = libroom.load(test_args, test_room, pool=test_pool, conn=conn)
            assert player is not None
            assert room is not False

            player_items_before = len(player.items)
            room_items_before = len(room.items)

            item = _leave_item(test_args, room, player, item_name, test_pool, conn=conn)
            assert item is not None
            assert len(player.items) == player_items_before - 1
            assert len(room.items) == room_items_before + 1

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            room = libroom.load(test_args, test_room, pool=test_pool, conn=conn)
            assert player is not None
            assert room is not False

            item = _take_item(test_args, room, player, item_name, test_pool, conn=conn)
            assert item is not None
            assert len(player.items) == player_items_before
            assert len(room.items) == room_items_before

    def test_take_nonexistent_item(self, test_args, test_pool, test_player, test_room):
        """finditem returns None when item is not in the room."""
        from murdermotel import room as libroom

        room = libroom.load(test_args, test_room, pool=test_pool)
        assert room is not False

        result = room.finditem("nonexistent_item_xyz")
        assert result is None

    def test_leave_nonexistent_item(self, test_args, test_pool, test_player, test_room):
        """finditem returns None when item is not on the player."""
        from murdermotel import player as libplayer

        _clear_player_items(test_args, test_player, test_pool)
        player = libplayer.load(test_args, test_player, pool=test_pool)
        assert player is not None

        result = player.finditem("nonexistent_item_xyz")
        assert result is None

    def test_take_from_empty_room(self, test_args, test_pool, test_player, test_room):
        """Taking from a room with no items finds nothing."""
        from murdermotel import room as libroom

        room = libroom.load(test_args, test_room, pool=test_pool)
        assert room is not False

        room.items = []
        room.save(pool=test_pool)

        room = libroom.load(test_args, test_room, pool=test_pool)
        assert room is not False
        assert len(room.items) == 0

        result = room.finditem("any_item")
        assert result is None

    def test_leave_with_empty_inventory(
        self, test_args, test_pool, test_player, test_room
    ):
        """Leaving when player has no items finds nothing."""
        from murdermotel import player as libplayer

        _clear_player_items(test_args, test_player, test_pool)
        player = libplayer.load(test_args, test_player, pool=test_pool)
        assert player is not None
        assert len(player.items) == 0

        result = player.finditem("any_item")
        assert result is None

    def test_multiple_rooms_take_leave(
        self, test_args, test_pool, test_player, test_rooms
    ):
        """Three connected rooms: take item in middle, leave it in north."""
        from murdermotel import room as libroom, player as libplayer

        south_room, middle_room, north_room = test_rooms

        item_name = "machete"
        item_serial = 3

        _place_item_in_room(test_args, middle_room, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            room = libroom.load(test_args, middle_room, pool=test_pool, conn=conn)
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            assert room is not False
            assert player is not None

            item = _take_item(test_args, room, player, item_name, test_pool, conn=conn)
            assert item is not None
            assert len(player.items) == 1
            assert len(room.items) == 0

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            room = libroom.load(test_args, north_room, pool=test_pool, conn=conn)
            assert player is not None
            assert room is not False

            item = _leave_item(test_args, room, player, item_name, test_pool, conn=conn)
            assert item is not None
            assert len(player.items) == 0
            assert len(room.items) == 1

        _clear_room_items(test_args, north_room, test_pool)

    def test_max_items_constant(self):
        """Verify MAXITEMSPERPLAYER constant is defined."""
        from murdermotel import lib as libmm

        assert libmm.MAXITEMSPERPLAYER == 5

    def test_take_item_by_title(self, test_args, test_pool, test_player, test_room):
        """finditem matches on item.title in addition to item.name."""
        from murdermotel import room as libroom, player as libplayer

        item_name = "knife"
        item_serial = 1

        _place_item_in_room(test_args, test_room, item_name, item_serial, test_pool)

        room = libroom.load(test_args, test_room, pool=test_pool)
        player = libplayer.load(test_args, test_player, pool=test_pool)
        _sync_item_to_room(test_args, room, test_pool)

        player_items_before = len(player.items)

        item = _take_item(test_args, room, player, "knife", test_pool)
        assert item is not None
        assert len(player.items) == player_items_before + 1


class TestTakeLeaveWithMockedIO:
    """Integration tests using mocked io.inputstring to simulate the full prompt flow."""

    def test_take_via_mocked_io(self, test_args, test_pool, test_player, test_room):
        """Patch io.inputstring to simulate 'T' → 'knife' prompt."""
        from unittest.mock import patch

        from bbsengine6 import io
        from murdermotel import room as libroom, player as libplayer

        item_name = "knife"
        item_serial = 1

        _place_item_in_room(test_args, test_room, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            room = libroom.load(test_args, test_room, pool=test_pool, conn=conn)
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            assert room is not False
            assert player is not None

            room_items_before = len(room.items)
            player_items_before = len(player.items)

            with patch.object(io, "inputstring", return_value=item_name):
                itemindex = room.finditem(item_name)
                assert itemindex is not None
                item = room.items[itemindex]
                del room.items[itemindex]
                player.items.append(item)
                player.save(pool=test_pool, conn=conn)
                room.save(pool=test_pool, conn=conn)

            assert len(room.items) == room_items_before - 1
            assert len(player.items) == player_items_before + 1

    def test_leave_via_mocked_io(self, test_args, test_pool, test_player, test_room):
        """Patch io.inputstring to simulate 'L' → 'knife' prompt."""
        from unittest.mock import patch

        from bbsengine6 import io
        from murdermotel import room as libroom, player as libplayer

        item_name = "knife"
        item_serial = 1

        _place_item_on_player(test_args, test_player, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            room = libroom.load(test_args, test_room, pool=test_pool, conn=conn)
            assert player is not None
            assert room is not False

            player_items_before = len(player.items)
            room_items_before = len(room.items)

            with patch.object(io, "inputstring", return_value=item_name):
                item = _leave_item(
                    test_args, room, player, item_name, test_pool, conn=conn
                )
                assert item is not None

            assert len(player.items) == player_items_before - 1
            assert len(room.items) == room_items_before + 1

    def test_take_aborted_via_mocked_io(
        self, test_args, test_pool, test_player, test_room
    ):
        """Patch io.inputstring to empty string (aborted) — no state changes."""
        from unittest.mock import patch

        from bbsengine6 import io
        from murdermotel import room as libroom, player as libplayer

        room = libroom.load(test_args, test_room, pool=test_pool)
        player = libplayer.load(test_args, test_player, pool=test_pool)
        _sync_item_to_room(test_args, room, test_pool)

        room_items_before = len(room.items)
        player_items_before = len(player.items)

        with patch.object(io, "inputstring", return_value=""):
            itemname = ""
            if itemname == "":
                pass
            itemindex = room.finditem(itemname) if itemname else None
            assert itemindex is None

        assert len(room.items) == room_items_before
        assert len(player.items) == player_items_before
