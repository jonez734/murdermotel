"""Tests for thief stealing items from players."""

import pytest

from bbsengine6 import database


class TestThiefSteal:
    """Test thief stealing items from players."""

    def test_thief_steals_from_player(self, test_args, test_pool):
        """Test thief can steal item from player."""
        from murdermotel import thief as libthief
        from murdermotel import player as libplayer

        player_moniker = "victim_player"
        item_name = "knife"
        item_serial = 1

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    """
                    INSERT INTO $murdermotel.player (moniker, roomid, turn, moves, points, bodycount)
                    VALUES (:moniker, 1, 1, 10, 0, 0)
                    ON CONFLICT (moniker) DO NOTHING
                """,
                    moniker=player_moniker,
                )
                cur.execute(q, {"moniker": player_moniker})
                q = database.query(
                    """
                    INSERT INTO $murdermotel.map_item_player 
                    (playermoniker, itemname, serial)
                    VALUES (:playermoniker, :itemname, :serial)
                """,
                    playermoniker=player_moniker,
                    itemname=item_name,
                    serial=item_serial,
                )
                cur.execute(q, {"playermoniker": player_moniker, "itemname": item_name, "serial": item_serial})
            conn.commit()

        try:
            player_before = libplayer.load(test_args, player_moniker, pool=test_pool)
            assert any(i.name == item_name for i in player_before.items)

            thief = libthief.load(test_args, "thief", pool=test_pool)
            assert thief is not False

            stolen = thief.steal_from_player(test_args, player_moniker, item_name, pool=test_pool)

            player_after = libplayer.load(test_args, player_moniker, pool=test_pool)
            if stolen:
                assert not any(i.name == item_name for i in player_after.items)
        finally:
            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM $murdermotel.map_item_player WHERE playermoniker = :moniker",
                        moniker=player_moniker,
                    )
                    cur.execute(q, {"moniker": player_moniker})
                    q = database.query(
                        "DELETE FROM $murdermotel.player WHERE moniker = :moniker",
                        moniker=player_moniker,
                    )
                    cur.execute(q, {"moniker": player_moniker})
                conn.commit()

    def test_thief_steals_from_room(self, test_args, test_pool, test_room):
        """Test thief can steal item from room."""
        from murdermotel import thief as libthief
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
            room_before = libroom.load(test_args, test_room, pool=test_pool)
            assert any(i.name == item_name for i in room_before.items)

            thief = libthief.load(test_args, "thief", pool=test_pool)
            assert thief is not False

            stolen = thief.steal_from_room(test_args, test_room, item_name, pool=test_pool)

            room_after = libroom.load(test_args, test_room, pool=test_pool)
            if stolen:
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
                conn.commit()

    def test_thief_steals_nothing(self, test_args, test_pool):
        """Test thief stealing from player with no items returns empty."""
        from murdermotel import thief as libthief
        from murdermotel import player as libplayer

        player_moniker = "empty_player"

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    """
                    INSERT INTO $murdermotel.player (moniker, roomid, turn, moves, points, bodycount)
                    VALUES (:moniker, 1, 1, 10, 0, 0)
                    ON CONFLICT (moniker) DO NOTHING
                """,
                    moniker=player_moniker,
                )
                cur.execute(q, {"moniker": player_moniker})
            conn.commit()

        try:
            player = libplayer.load(test_args, player_moniker, pool=test_pool)
            assert len(player.items) == 0

            thief = libthief.load(test_args, "thief", pool=test_pool)
            stolen = thief.steal_from_player(test_args, player_moniker, "any_item", pool=test_pool)

            assert stolen == []
        finally:
            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM $murdermotel.player WHERE moniker = :moniker",
                        moniker=player_moniker,
                    )
                    cur.execute(q, {"moniker": player_moniker})
                conn.commit()
