"""Tests verifying thief.item maps are set up correctly when stealing.

These tests verify that when `thief.steal_from_player()` moves an item from
a player to the thief, the database state is correct:

    map_item_player  → row deleted for that item
    map_item_thief   → row inserted with the stolen item
    map_item_room    → unchanged

In-memory state is also verified:
    player.items → item removed
    thief.items  → item added

The tests use `pool=test_pool` (no conn=) so steal_from_player() opens its own
connection and commits, which is the standard production path.  Calling
steal_from_player(conn=conn) without also committing inside steal_from_player
leaves changes uncommitted on the caller's connection and is therefore avoided.
"""

from __future__ import annotations

import pytest

from bbsengine6 import database


_ITEMS = {
    "ruby": (77, 1, 99),
    "emerald": (88, 2),
    "sapphire": (55, 3),
    "diamond": (11,),
    "pearl": (22,),
    "opal": (33,),
    "topaz": (44,),
    "jade": (99,),
    "gold_ring": (66,),
    "gem1": (1,),
    "gem8": (1,),
}


def _cleanup_item_table(args, pool):
    with database.connect(args, pool=pool) as conn:
        with database.cursor(conn) as cur:
            for name, serials in _ITEMS.items():
                for serial in serials:
                    q = database.query(
                        "DELETE FROM $murdermotel.item WHERE name = :name AND serial = :serial",
                        name=name,
                        serial=serial,
                    )
                    cur.execute(q, {"name": name, "serial": serial})
        conn.commit()


def _cleanup_all_map_tables(args, pool):
    with database.connect(args, pool=pool) as conn:
        with database.cursor(conn) as cur:
            for name, serials in _ITEMS.items():
                for serial in serials:
                    q = database.query(
                        "DELETE FROM $murdermotel.map_item_room WHERE itemname = :name AND serial = :serial",
                        name=name,
                        serial=serial,
                    )
                    cur.execute(q, {"name": name, "serial": serial})
                    q = database.query(
                        "DELETE FROM $murdermotel.map_item_player WHERE itemname = :name AND serial = :serial",
                        name=name,
                        serial=serial,
                    )
                    cur.execute(q, {"name": name, "serial": serial})
        conn.commit()


def _cleanup_all_test_items(args, pool):
    _cleanup_all_map_tables(args, pool)
    _cleanup_item_table(args, pool)


def _place_item_on_player(args, playermoniker, itemname, serial, pool, conn=None):
    def _work(c):
        with database.cursor(c) as cur:
            q = database.query(
                "INSERT INTO $murdermotel.item (name, serial, title, kind) "
                "VALUES (:name, :serial, :title, 'item') "
                "ON CONFLICT (name, serial) DO UPDATE SET title = EXCLUDED.title",
                name=itemname,
                serial=serial,
                title=itemname,
            )
            cur.execute(q, {"name": itemname, "serial": serial, "title": itemname})
            q = database.query(
                "INSERT INTO $murdermotel.map_item_player "
                "(playermoniker, itemname, serial) "
                "VALUES (:playermoniker, :itemname, :serial) "
                "ON CONFLICT DO NOTHING",
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


def _db_player_items(args, playermoniker, pool, conn=None):
    def _work(c):
        with database.cursor(c) as cur:
            q = database.query(
                "SELECT itemname, serial FROM $murdermotel.map_item_player "
                "WHERE playermoniker = :playermoniker",
                playermoniker=playermoniker,
            )
            cur.execute(q, {"playermoniker": playermoniker})
            if cur.rowcount == 0:
                return []
            return cur.fetchall()

    if conn is None:
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def _db_thief_items(args, pool, conn=None):
    def _work(c):
        with database.cursor(c) as cur:
            q = database.query(
                "SELECT itemname, serial FROM $murdermotel.map_item_thief "
                "WHERE thiefname = 'thief'",
            )
            cur.execute(q)
            if cur.rowcount == 0:
                return []
            return cur.fetchall()

    if conn is None:
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def _db_room_items(args, roomid, pool, conn=None):
    def _work(c):
        with database.cursor(c) as cur:
            q = database.query(
                "SELECT itemname, serial FROM $murdermotel.map_item_room "
                "WHERE roomid = :roomid",
                roomid=roomid,
            )
            cur.execute(q, {"roomid": roomid})
            if cur.rowcount == 0:
                return []
            return cur.fetchall()

    if conn is None:
        with database.connect(args, pool=pool) as conn:
            return _work(conn)
    return _work(conn)


def _clear_player_items(args, playermoniker, pool):
    with database.connect(args, pool=pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                "DELETE FROM $murdermotel.map_item_player WHERE playermoniker = :playermoniker",
                playermoniker=playermoniker,
            )
            cur.execute(q, {"playermoniker": playermoniker})
        conn.commit()


def _clear_thief_items(args, pool):
    with database.connect(args, pool=pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                "DELETE FROM $murdermotel.map_item_thief WHERE thiefname = 'thief'"
            )
            cur.execute(q)
        conn.commit()


class TestThiefMapStealBasics:
    def test_steal_removes_row_from_map_item_player(
        self, test_args, test_pool, test_player
    ):
        from murdermotel import player as libplayer, thief as libthief

        _clear_player_items(test_args, test_player, test_pool)
        _clear_thief_items(test_args, test_pool)
        _cleanup_all_test_items(test_args, test_pool)

        item_name = "ruby"
        item_serial = 77

        _place_item_on_player(test_args, test_player, item_name, item_serial, test_pool)

        db_rows = _db_player_items(test_args, test_player, test_pool)
        assert len(db_rows) == 1
        assert db_rows[0]["itemname"] == item_name
        assert db_rows[0]["serial"] == item_serial

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            thief = libthief.load(test_args, pool=test_pool, conn=conn)
            if player is None or thief is None:
                pytest.skip("Player or thief not loaded")

            db_rows = _db_player_items(test_args, test_player, test_pool, conn=conn)
            assert len(db_rows) == 1

            stolen = libthief.steal_from_player(player, thief, pool=test_pool)
            conn.commit()

        assert stolen is not None
        assert stolen.name == item_name
        assert stolen.serial == item_serial

        db_rows_after = _db_player_items(test_args, test_player, test_pool)
        assert len(db_rows_after) == 0

    def test_steal_inserts_row_into_map_item_thief(
        self, test_args, test_pool, test_player
    ):
        from murdermotel import player as libplayer, thief as libthief

        _clear_player_items(test_args, test_player, test_pool)
        _clear_thief_items(test_args, test_pool)
        _cleanup_all_test_items(test_args, test_pool)

        item_name = "emerald"
        item_serial = 88

        _place_item_on_player(test_args, test_player, item_name, item_serial, test_pool)

        db_rows_before = _db_thief_items(test_args, test_pool)
        assert len(db_rows_before) == 0

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            thief = libthief.load(test_args, pool=test_pool, conn=conn)
            if player is None or thief is None:
                pytest.skip("Player or thief not loaded")

            stolen = libthief.steal_from_player(player, thief, pool=test_pool)
            conn.commit()

        assert stolen is not None

        db_rows_after = _db_thief_items(test_args, test_pool)
        assert len(db_rows_after) == 1
        assert db_rows_after[0]["itemname"] == item_name
        assert db_rows_after[0]["serial"] == item_serial

    def test_steal_preserves_map_item_room(
        self, test_args, test_pool, test_player, test_room
    ):
        from murdermotel import player as libplayer, thief as libthief

        _clear_player_items(test_args, test_player, test_pool)
        _clear_thief_items(test_args, test_pool)
        _cleanup_all_test_items(test_args, test_pool)

        player_item_name = "sapphire"
        player_item_serial = 55

        room_item_name = "gold_ring"
        room_item_serial = 66

        _place_item_on_player(
            test_args, test_player, player_item_name, player_item_serial, test_pool
        )

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    "INSERT INTO $murdermotel.item (name, serial, title, kind) "
                    "VALUES (:name, :serial, :title, 'item') "
                    "ON CONFLICT (name, serial) DO UPDATE SET title = EXCLUDED.title",
                    name=room_item_name,
                    serial=room_item_serial,
                    title=room_item_name,
                )
                cur.execute(
                    q,
                    {
                        "name": room_item_name,
                        "serial": room_item_serial,
                        "title": room_item_name,
                    },
                )
                q = database.query(
                    "INSERT INTO $murdermotel.map_item_room "
                    "(roomid, itemname, serial) "
                    "VALUES (:roomid, :itemname, :serial) "
                    "ON CONFLICT DO NOTHING",
                    roomid=test_room,
                    itemname=room_item_name,
                    serial=room_item_serial,
                )
                cur.execute(
                    q,
                    {
                        "roomid": test_room,
                        "itemname": room_item_name,
                        "serial": room_item_serial,
                    },
                )
            conn.commit()

        room_items_before = _db_room_items(test_args, test_room, test_pool)
        assert len(room_items_before) == 1
        assert room_items_before[0]["itemname"] == room_item_name

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            thief = libthief.load(test_args, pool=test_pool, conn=conn)
            if player is None or thief is None:
                pytest.skip("Player or thief not loaded")

            stolen = libthief.steal_from_player(player, thief, pool=test_pool)
            conn.commit()

        assert stolen is not None

        room_items_after = _db_room_items(test_args, test_room, test_pool)
        assert len(room_items_after) == 1
        assert room_items_after[0]["itemname"] == room_item_name


class TestThiefMapStealInMemory:
    def test_steal_removes_item_from_player_items_list(
        self, test_args, test_pool, test_player
    ):
        from murdermotel import player as libplayer, thief as libthief

        _clear_player_items(test_args, test_player, test_pool)
        _clear_thief_items(test_args, test_pool)
        _cleanup_all_test_items(test_args, test_pool)

        item_name = "diamond"
        item_serial = 11

        _place_item_on_player(test_args, test_player, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            thief = libthief.load(test_args, pool=test_pool, conn=conn)
            if player is None or thief is None:
                pytest.skip("Player or thief not loaded")

            player_items_before = len(player.items)
            stolen = libthief.steal_from_player(player, thief, pool=test_pool)
            conn.commit()

            assert stolen is not None
            assert len(player.items) == player_items_before - 1

    def test_steal_adds_item_to_thief_items_list(
        self, test_args, test_pool, test_player
    ):
        from murdermotel import player as libplayer, thief as libthief

        _clear_player_items(test_args, test_player, test_pool)
        _clear_thief_items(test_args, test_pool)
        _cleanup_all_test_items(test_args, test_pool)

        item_name = "pearl"
        item_serial = 22

        _place_item_on_player(test_args, test_player, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            thief = libthief.load(test_args, pool=test_pool, conn=conn)
            if player is None or thief is None:
                pytest.skip("Player or thief not loaded")

            thief_items_before = len(thief.items)
            stolen = libthief.steal_from_player(player, thief, pool=test_pool)
            conn.commit()

            assert stolen is not None
            assert len(thief.items) == thief_items_before + 1
            assert any(
                i.name == item_name and i.serial == item_serial for i in thief.items
            )


class TestThiefMapStealReload:
    def test_stolen_item_reloads_via_thief_load(
        self, test_args, test_pool, test_player
    ):
        from murdermotel import player as libplayer, thief as libthief

        _clear_player_items(test_args, test_player, test_pool)
        _clear_thief_items(test_args, test_pool)
        _cleanup_all_test_items(test_args, test_pool)

        item_name = "opal"
        item_serial = 33

        _place_item_on_player(test_args, test_player, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            thief = libthief.load(test_args, pool=test_pool, conn=conn)
            if player is None or thief is None:
                pytest.skip("Player or thief not loaded")

            libthief.steal_from_player(player, thief, pool=test_pool)
            conn.commit()

        with test_pool.getconn() as conn:
            thief_reloaded = libthief.load(test_args, pool=test_pool, conn=conn)
            if thief_reloaded is None:
                pytest.fail("Thief did not reload after steal")

            assert len(thief_reloaded.items) == 1
            assert thief_reloaded.items[0].name == item_name
            assert thief_reloaded.items[0].serial == item_serial

    def test_player_loads_with_empty_inventory_after_steal(
        self, test_args, test_pool, test_player
    ):
        from murdermotel import player as libplayer, thief as libthief

        _clear_player_items(test_args, test_player, test_pool)
        _clear_thief_items(test_args, test_pool)
        _cleanup_all_test_items(test_args, test_pool)

        item_name = "topaz"
        item_serial = 44

        _place_item_on_player(test_args, test_player, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            thief = libthief.load(test_args, pool=test_pool, conn=conn)
            if player is None or thief is None:
                pytest.skip("Player or thief not loaded")

            libthief.steal_from_player(player, thief, pool=test_pool)
            conn.commit()

        with test_pool.getconn() as conn:
            player_reloaded = libplayer.load(
                test_args, test_player, pool=test_pool, conn=conn
            )
            if player_reloaded is None:
                pytest.fail("Player did not reload after theft")

            assert len(player_reloaded.items) == 0


class TestThiefMapStealSerial:
    def test_stolen_item_preserves_serial_in_map_item_thief(
        self, test_args, test_pool, test_player
    ):
        from murdermotel import player as libplayer, thief as libthief

        _clear_player_items(test_args, test_player, test_pool)
        _clear_thief_items(test_args, test_pool)
        _cleanup_all_test_items(test_args, test_pool)

        item_name = "jade"
        item_serial = 99

        _place_item_on_player(test_args, test_player, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            thief = libthief.load(test_args, pool=test_pool, conn=conn)
            if player is None or thief is None:
                pytest.skip("Player or thief not loaded")

            stolen = libthief.steal_from_player(player, thief, pool=test_pool)
            conn.commit()

        assert stolen is not None
        assert stolen.serial == item_serial

        db_rows = _db_thief_items(test_args, test_pool)
        assert len(db_rows) == 1
        assert db_rows[0]["serial"] == item_serial


class TestThiefMapStealMultipleItems:
    def test_steal_one_of_multiple_player_items(
        self, test_args, test_pool, test_player
    ):
        from murdermotel import player as libplayer, thief as libthief

        _clear_player_items(test_args, test_player, test_pool)
        _clear_thief_items(test_args, test_pool)
        _cleanup_all_test_items(test_args, test_pool)

        items = [
            ("ruby", 1),
            ("emerald", 2),
            ("sapphire", 3),
        ]

        for name, serial in items:
            _place_item_on_player(test_args, test_player, name, serial, test_pool)

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            thief = libthief.load(test_args, pool=test_pool, conn=conn)
            if player is None or thief is None:
                pytest.skip("Player or thief not loaded")

            player_items_before = len(player.items)
            stolen = libthief.steal_from_player(player, thief, pool=test_pool)
            conn.commit()

            assert stolen is not None
            assert len(player.items) == player_items_before - 1

        db_rows_after = _db_player_items(test_args, test_player, test_pool)
        assert len(db_rows_after) == 2

        db_thief_rows = _db_thief_items(test_args, test_pool)
        assert len(db_thief_rows) == 1

    def test_thief_load_reloads_all_stolen_items(
        self, test_args, test_pool, test_player
    ):
        _clear_player_items(test_args, test_player, test_pool)
        _clear_thief_items(test_args, test_pool)
        _cleanup_all_test_items(test_args, test_pool)
        _place_item_on_player(test_args, test_player, "gem1", 1, test_pool)

        with test_pool.getconn() as conn:
            from murdermotel import player as libplayer, thief as libthief

            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            thief = libthief.load(test_args, pool=test_pool, conn=conn)
            if player is None or thief is None:
                pytest.skip("Player or thief not loaded")
            libthief.steal_from_player(player, thief, pool=test_pool)
            conn.commit()

        with test_pool.getconn() as conn:
            thief_reloaded = libthief.load(test_args, pool=test_pool, conn=conn)
            assert thief_reloaded is not None
            assert len(thief_reloaded.items) == 1
            assert thief_reloaded.items[0].name == "gem1"


class TestThiefMapStealEdgeCases:
    def test_steal_empty_player_returns_none(self, test_args, test_pool, test_player):
        from murdermotel import player as libplayer, thief as libthief

        _clear_player_items(test_args, test_player, test_pool)
        _clear_thief_items(test_args, test_pool)
        _cleanup_all_test_items(test_args, test_pool)

        with test_pool.getconn() as conn:
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            thief = libthief.load(test_args, pool=test_pool, conn=conn)
            if player is None or thief is None:
                pytest.skip("Player or thief not loaded")

            stolen = libthief.steal_from_player(player, thief, pool=test_pool)

            assert stolen is None
