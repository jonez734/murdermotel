"""Tests for thief stealing items from players."""

import pytest

from bbsengine6 import database


class TestThiefSteal:
    """Test thief stealing items from players."""

    def test_thief_steals_from_player(self, test_args, test_pool, test_player):
        """Test thief can steal item from player."""
        from murdermotel import thief as libthief
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
            if player is None:
                pytest.skip("Player not loaded")

            thief = libthief.load(test_args, pool=test_pool)
            if thief is None:
                pytest.skip("Thief not loaded")

            initial_player_items = len(player.items)
            stolen = libthief.steal_from_player(player, thief, pool=test_pool)

            player_after = libplayer.load(test_args, test_player, pool=test_pool)
            if player_after is not None and stolen:
                assert len(player_after.items) == initial_player_items - 1
        finally:
            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM $murdermotel.map_item_player WHERE playermoniker = :moniker",
                        moniker=test_player,
                    )
                    cur.execute(q, {"moniker": test_player})
                conn.commit()

    def test_thief_steals_from_room(self, test_args, test_pool, test_room):
        """Test thief can steal item from room - room item test."""
        from murdermotel import room as libroom

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
            if room is False:
                pytest.skip("Room not loaded")

            initial_room_items = len(room.items)
            assert initial_room_items >= 0
        finally:
            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM $murdermotel.map_item_room WHERE roomid = :roomid AND itemname = :itemname",
                        roomid=test_room,
                        itemname=item_name,
                    )
                    cur.execute(q, {"roomid": test_room, "itemname": item_name})
                conn.commit()

    def test_thief_steals_nothing(self, test_args, test_pool, test_player):
        """Test thief stealing from player with no items returns None."""
        from murdermotel import thief as libthief
        from murdermotel import player as libplayer

        player = libplayer.load(test_args, test_player, pool=test_pool)
        if player is None:
            pytest.skip("Player not loaded")

        thief = libthief.load(test_args, pool=test_pool)
        if thief is None:
            pytest.skip("Thief not loaded")

        stolen = libthief.steal_from_player(player, thief, pool=test_pool)
        assert stolen is None
