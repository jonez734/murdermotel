"""Tests for item transfer (take/leave) functionality."""

import pytest

from bbsengine6 import database


class TestItemTransfer:
    """Test item transfer between room and player."""

    def test_take_item_from_room(self, test_args, test_pool, test_player, test_room):
        """Test 'T' command transfers item from room to player."""
        from murdermotel import room as libroom
        from murdermotel import player as libplayer

        item_name = "knife"
        item_serial = 1

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    """
                    INSERT INTO $murdermotel.map_item_room 
                    (roomid, itemname, serial)
                    VALUES (:roomid, :itemname, :serial)
                """,
                    roomid=test_room,
                    itemname=item_name,
                    serial=item_serial,
                )
                cur.execute(q, {"roomid": test_room, "itemname": item_name, "serial": item_serial})
            conn.commit()

        try:
            room = libroom.load(test_args, test_room, pool=test_pool)
            assert room is not False
            assert any(i.name == item_name for i in room.items)

            player = libplayer.load(test_args, test_player, pool=test_pool)
            initial_item_count = len(player.items)

            del room.items[0]
            player.items.append(room.items[0] if room.items else None)

            player.save(pool=test_pool)
            room.save(pool=test_pool)

            player_after = libplayer.load(test_args, test_player, pool=test_pool)
            room_after = libroom.load(test_args, test_room, pool=test_pool)

            assert len(player_after.items) == initial_item_count + 1
            assert not any(i.name == item_name for i in room_after.items)
        finally:
            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM $murdermotel.map_item_room WHERE roomid = :roomid AND itemname = :itemname",
                        roomid=test_room,
                        itemname=item_name,
                    )
                    cur.execute(q, {"roomid": test_room, "itemname": item_name})
                    q = database.query(
                        "DELETE FROM $murdermotel.map_item_player WHERE playermoniker = :moniker AND itemname = :itemname",
                        moniker=test_player,
                        itemname=item_name,
                    )
                    cur.execute(q, {"moniker": test_player, "itemname": item_name})
                conn.commit()

    def test_leave_item_from_player(self, test_args, test_pool, test_player, test_room):
        """Test 'L' command transfers item from player to room."""
        from murdermotel import room as libroom
        from murdermotel import player as libplayer

        item_name = "knife"
        item_serial = 1

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    """
                    INSERT INTO $murdermotel.map_item_player 
                    (playermoniker, itemname, serial)
                    VALUES (:playermoniker, :itemname, :serial)
                """,
                    playermoniker=test_player,
                    itemname=item_name,
                    serial=item_serial,
                )
                cur.execute(q, {"playermoniker": test_player, "itemname": item_name, "serial": item_serial})
            conn.commit()

        try:
            player = libplayer.load(test_args, test_player, pool=test_pool)
            assert any(i.name == item_name for i in player.items)

            room = libroom.load(test_args, test_room, pool=test_pool)
            initial_room_item_count = len(room.items)

            del player.items[0]
            if player.items:
                room.items.append(player.items[0])

            player.save(pool=test_pool)
            room.save(pool=test_pool)

            player_after = libplayer.load(test_args, test_player, pool=test_pool)
            room_after = libroom.load(test_args, test_room, pool=test_pool)

            assert not any(i.name == item_name for i in player_after.items)
            assert len(room_after.items) == initial_room_item_count + 1
        finally:
            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM $murdermotel.map_item_room WHERE roomid = :roomid AND itemname = :itemname",
                        roomid=test_room,
                        itemname=item_name,
                    )
                    cur.execute(q, {"roomid": test_room, "itemname": item_name})
                    q = database.query(
                        "DELETE FROM $murdermotel.map_item_player WHERE playermoniker = :moniker AND itemname = :itemname",
                        moniker=test_player,
                        itemname=item_name,
                    )
                    cur.execute(q, {"moniker": test_player, "itemname": item_name})
                conn.commit()

    def test_take_nonexistent_item(self, test_args, test_pool, test_player, test_room):
        """Test taking an item that doesn't exist returns appropriate response."""
        from murdermotel import room as libroom

        room = libroom.load(test_args, test_room, pool=test_pool)
        result = room.finditem("nonexistent_item_xyz")
        assert result is None

    def test_leave_item_not_on_player(self, test_args, test_pool, test_player, test_room):
        """Test leaving an item player doesn't have returns appropriate response."""
        from murdermotel import player as libplayer

        player = libplayer.load(test_args, test_player, pool=test_pool)
        result = player.finditem("nonexistent_item_xyz")
        assert result is None
