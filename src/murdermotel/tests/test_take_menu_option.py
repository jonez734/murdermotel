"""Integration tests for the [T]ake item menu option.

Verifies that:
1. The 'T' option appears in the menu when a room has items
2. Items can be taken from a room to the player's inventory
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


def _cleanup_test_items(args, pool):
    from bbsengine6 import database

    if args is None or pool is None:
        return

    with database.connect(args, pool=pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                "DELETE FROM $murdermotel.map_item_room WHERE roomid = :roomid",
                roomid=9999,
            )
            cur.execute(q, {"roomid": 9999})
            q = database.query(
                "DELETE FROM $murdermotel.map_item_player WHERE playermoniker = :moniker",
                moniker="test_player_murdermotel",
            )
            cur.execute(q, {"moniker": "test_player_murdermotel"})
        conn.commit()

    with database.connect(args, pool=pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                "DELETE FROM $murdermotel.item WHERE name = :name AND serial = :serial",
                name="test_item_teardown",
                serial=999,
            )
            cur.execute(q, {"name": "test_item_teardown", "serial": 999})
        conn.commit()


def _sync_room_items(args, room, pool):
    from murdermotel import room as libroom

    fresh = libroom.load(args, room.id, pool=pool)
    if fresh and fresh.items:
        room.items = fresh.items


def _take_item(args, room, player, itemname, pool, conn=None):
    itemindex = room.finditem(itemname)
    if itemindex is None:
        return None
    item = room.items[itemindex]
    del room.items[itemindex]
    player.items.append(item)
    player.save(pool=pool, conn=conn)
    room.save(pool=pool, conn=conn)
    return item


def _build_menu_options(room, player, libmm):
    options = ""
    if room.exits.get("north"):
        options += "N"
    if room.exits.get("west"):
        options += "W"
    if room.exits.get("east"):
        options += "E"
    if room.exits.get("south"):
        options += "S"
    if room.exits.get("up"):
        options += "U"
    if room.exits.get("down"):
        options += "D"
    if len(room.items) > 0 and len(player.items) <= libmm.MAXITEMSPERPLAYER:
        options += "T"
    if len(player.items) > 0:
        options += "L"
    options += "I"
    return "".join(sorted(options))


class TestTakeMenuOption:
    def test_t_option_available_when_room_has_items(
        self, test_args, test_pool, test_player, test_room
    ):
        from murdermotel import room as libroom, player as libplayer, lib as libmm

        item_name = "test_item_teardown"
        item_serial = 999
        _cleanup_test_items(test_args, test_pool)
        _place_item_in_room(test_args, test_room, item_name, item_serial, test_pool)

        room = libroom.load(test_args, test_room, pool=test_pool)
        player = libplayer.load(test_args, test_player, pool=test_pool)
        assert room is not False
        assert player is not None

        _sync_room_items(test_args, room, test_pool)
        assert len(room.items) > 0

        options = _build_menu_options(room, player, libmm)
        assert "T" in options, f"'T' option not in menu options: {options}"

        _clear_room_items(test_args, test_room, test_pool)
        _cleanup_test_items(test_args, test_pool)

    def test_t_option_not_available_when_room_is_empty(
        self, test_args, test_pool, test_player, test_room
    ):
        from murdermotel import room as libroom, player as libplayer, lib as libmm

        room = libroom.load(test_args, test_room, pool=test_pool)
        player = libplayer.load(test_args, test_player, pool=test_pool)
        assert room is not False
        assert player is not None

        room.items = []
        options = _build_menu_options(room, player, libmm)
        assert "T" not in options, (
            f"'T' option should not be in menu options: {options}"
        )

    def test_t_option_not_available_when_player_has_max_items(
        self, test_args, test_pool, test_player, test_room
    ):
        from murdermotel import room as libroom, player as libplayer, lib as libmm

        item_name = "test_item_teardown"
        item_serial = 999
        _cleanup_test_items(test_args, test_pool)
        _place_item_in_room(test_args, test_room, item_name, item_serial, test_pool)

        room = libroom.load(test_args, test_room, pool=test_pool)
        player = libplayer.load(test_args, test_player, pool=test_pool)
        assert room is not False
        assert player is not None

        _sync_room_items(test_args, room, test_pool)
        assert len(room.items) > 0

        player.items = [None] * (libmm.MAXITEMSPERPLAYER + 1)

        options = _build_menu_options(room, player, libmm)
        assert "T" not in options, (
            f"'T' option should not be available when player exceeds max items: {options}"
        )

        _clear_room_items(test_args, test_room, test_pool)
        _cleanup_test_items(test_args, test_pool)


class TestTakeItemFlow:
    def test_take_item_from_room_updates_inventory(
        self, test_args, test_pool, test_player, test_room
    ):
        from murdermotel import room as libroom, player as libplayer

        item_name = "test_item_teardown"
        item_serial = 999
        _cleanup_test_items(test_args, test_pool)
        _place_item_in_room(test_args, test_room, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            room = libroom.load(test_args, test_room, pool=test_pool, conn=conn)
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            assert room is not False
            assert player is not None

            _sync_room_items(test_args, room, test_pool)

            room_items_before = len(room.items)
            player_items_before = len(player.items)

            item = _take_item(test_args, room, player, item_name, test_pool, conn=conn)
            assert item is not None
            assert item.name == item_name
            assert len(room.items) == room_items_before - 1
            assert len(player.items) == player_items_before + 1

        _clear_room_items(test_args, test_room, test_pool)
        _cleanup_test_items(test_args, test_pool)

    def test_take_item_persists_after_reload(
        self, test_args, test_pool, test_player, test_room
    ):
        from murdermotel import room as libroom, player as libplayer

        item_name = "test_item_teardown"
        item_serial = 999
        _cleanup_test_items(test_args, test_pool)
        _place_item_in_room(test_args, test_room, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            room = libroom.load(test_args, test_room, pool=test_pool, conn=conn)
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            _sync_room_items(test_args, room, test_pool)

            _take_item(test_args, room, player, item_name, test_pool, conn=conn)

        with test_pool.getconn() as conn:
            room_reloaded = libroom.load(
                test_args, test_room, pool=test_pool, conn=conn
            )
            player_reloaded = libplayer.load(
                test_args, test_player, pool=test_pool, conn=conn
            )
            assert room_reloaded is not False
            assert player_reloaded is not None

            _sync_room_items(test_args, room_reloaded, test_pool)

            assert len(room_reloaded.items) == 0
            assert len(player_reloaded.items) == 1
            assert player_reloaded.items[0].name == item_name

        _clear_room_items(test_args, test_room, test_pool)
        _cleanup_test_items(test_args, test_pool)

    def test_take_item_updates_db_tables(
        self, test_args, test_pool, test_player, test_room
    ):
        from bbsengine6 import database
        from murdermotel import room as libroom, player as libplayer

        item_name = "test_item_teardown"
        item_serial = 999
        _cleanup_test_items(test_args, test_pool)
        _place_item_in_room(test_args, test_room, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            room = libroom.load(test_args, test_room, pool=test_pool, conn=conn)
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            _sync_room_items(test_args, room, test_pool)

            _take_item(test_args, room, player, item_name, test_pool, conn=conn)

            with database.cursor(conn) as cur:
                q = database.query(
                    "SELECT 1 FROM $murdermotel.map_item_room WHERE roomid = :roomid AND itemname = :itemname AND serial = :serial",
                    roomid=test_room,
                    itemname=item_name,
                    serial=item_serial,
                )
                cur.execute(
                    q,
                    {"roomid": test_room, "itemname": item_name, "serial": item_serial},
                )
                assert cur.rowcount == 0, "Item should be removed from map_item_room"

            with database.cursor(conn) as cur:
                q = database.query(
                    "SELECT 1 FROM $murdermotel.map_item_player WHERE playermoniker = :moniker AND itemname = :itemname AND serial = :serial",
                    moniker=test_player,
                    itemname=item_name,
                    serial=item_serial,
                )
                cur.execute(
                    q,
                    {
                        "moniker": test_player,
                        "itemname": item_name,
                        "serial": item_serial,
                    },
                )
                assert cur.rowcount == 1, "Item should be added to map_item_player"

        _clear_room_items(test_args, test_room, test_pool)
        _cleanup_test_items(test_args, test_pool)
