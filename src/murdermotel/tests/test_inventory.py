"""Test that pressing 'I' shows the player's inventory including taken items."""

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
                name="test_item_inventory",
                serial=998,
            )
            cur.execute(q, {"name": "test_item_inventory", "serial": 998})
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


class TestInventoryDisplay:
    def test_take_item_shows_in_inventory(
        self, test_args, test_pool, test_player, test_room
    ):
        from murdermotel import room as libroom, player as libplayer

        item_name = "test_item_inventory"
        item_serial = 998
        _cleanup_test_items(test_args, test_pool)
        _place_item_in_room(test_args, test_room, item_name, item_serial, test_pool)

        with test_pool.getconn() as conn:
            room = libroom.load(test_args, test_room, pool=test_pool, conn=conn)
            player = libplayer.load(test_args, test_player, pool=test_pool, conn=conn)
            assert room is not False
            assert player is not None

            _sync_room_items(test_args, room, test_pool)
            assert len(room.items) > 0

            _take_item(test_args, room, player, item_name, test_pool, conn=conn)

            player_items = player.getitems()
            player_item_names = [i.name for i in player_items]
            assert item_name in player_item_names, (
                f"Item '{item_name}' should be in player inventory.\n"
                f"Got: {player_item_names}"
            )

        _clear_room_items(test_args, test_room, test_pool)
        _cleanup_test_items(test_args, test_pool)