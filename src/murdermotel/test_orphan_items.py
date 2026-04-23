"""Tests for orphan item check and fix in startup.py"""

from bbsengine6 import database

from murdermotel import startup


class TestOrphanItems:
    """Test _check_orphan_items function."""

    def test_delete_orphaned_room_map_entries(self, test_args, test_pool):
        """Verify orphaned map_item_room entries are deleted."""
        orphan_item_name = "nonexistent_item_orphaned"
        orphan_serial = 999

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    "INSERT INTO $murdermotel.map_item_room (roomid, itemname, serial) VALUES (20, :name, :serial)",
                    name=orphan_item_name,
                    serial=orphan_serial,
                )
                cur.execute(q, {"name": orphan_item_name, "serial": orphan_serial})
            conn.commit()

        try:
            with database.connect(test_args, pool=test_pool) as conn:
                orphan_count, ghost_count = startup._check_orphan_items(test_args, conn)

            assert orphan_count >= 1, f"Expected at least 1 orphan, got {orphan_count}"

            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "SELECT * FROM $murdermotel.map_item_room WHERE itemname = :name AND serial = :serial",
                        name=orphan_item_name,
                        serial=orphan_serial,
                    )
                    cur.execute(q, {"name": orphan_item_name, "serial": orphan_serial})
                    remaining = cur.fetchall()

            assert len(remaining) == 0, f"Orphaned entry should be deleted: {remaining}"
        finally:
            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM $murdermotel.map_item_room WHERE itemname = :name AND serial = :serial",
                        name=orphan_item_name,
                        serial=orphan_serial,
                    )
                    cur.execute(q, {"name": orphan_item_name, "serial": orphan_serial})
                conn.commit()

    def test_delete_orphaned_player_map_entries(self, test_args, test_pool, test_player):
        """Verify orphaned map_item_player entries are deleted."""
        orphan_item_name = "nonexistent_item_player"
        orphan_serial = 998

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    "INSERT INTO $murdermotel.map_item_player (playermoniker, itemname, serial) VALUES (:playermoniker, :name, :serial)",
                    playermoniker=test_player,
                    name=orphan_item_name,
                    serial=orphan_serial,
                )
                cur.execute(q, {"playermoniker": test_player, "name": orphan_item_name, "serial": orphan_serial})
            conn.commit()

        try:
            with database.connect(test_args, pool=test_pool) as conn:
                orphan_count, ghost_count = startup._check_orphan_items(test_args, conn)

            assert orphan_count >= 1, f"Expected at least 1 orphan, got {orphan_count}"

            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "SELECT * FROM $murdermotel.map_item_player WHERE itemname = :name AND serial = :serial",
                        name=orphan_item_name,
                        serial=orphan_serial,
                    )
                    cur.execute(q, {"name": orphan_item_name, "serial": orphan_serial})
                    remaining = cur.fetchall()

            assert len(remaining) == 0, f"Orphaned entry should be deleted: {remaining}"
        finally:
            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM $murdermotel.map_item_player WHERE itemname = :name AND serial = :serial",
                        name=orphan_item_name,
                        serial=orphan_serial,
                    )
                    cur.execute(q, {"name": orphan_item_name, "serial": orphan_serial})
                conn.commit()

    def test_redisribute_ghost_items(self, test_args, test_pool):
        """Verify ghost items (in mm.item but not in any map) get redistributed."""
        ghost_item_name = "ghost_item_test"
        ghost_serial = 1
        ghost_kind = "component"

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    "INSERT INTO $murdermotel.item (name, kind, serial, title) VALUES (:name, :kind, :serial, 'Ghost Test Item')",
                    name=ghost_item_name,
                    kind=ghost_kind,
                    serial=ghost_serial,
                )
                cur.execute(q, {"name": ghost_item_name, "kind": ghost_kind, "serial": ghost_serial})
            conn.commit()

        try:
            with database.connect(test_args, pool=test_pool) as conn:
                orphan_count, ghost_count = startup._check_orphan_items(test_args, conn)

            assert ghost_count >= 1, f"Expected at least 1 ghost, got {ghost_count}"

            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "SELECT * FROM $murdermotel.map_item_room WHERE itemname = :name AND serial = :serial",
                        name=ghost_item_name,
                        serial=ghost_serial,
                    )
                    cur.execute(q, {"name": ghost_item_name, "serial": ghost_serial})
                    placed = cur.fetchall()

            assert len(placed) >= 1, f"Ghost item should be placed in a room, got {len(placed)} placements"
        finally:
            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM $murdermotel.map_item_room WHERE itemname = :name AND serial = :serial",
                        name=ghost_item_name,
                        serial=ghost_serial,
                    )
                    cur.execute(q, {"name": ghost_item_name, "serial": ghost_serial})
                    q = database.query(
                        "DELETE FROM $murdermotel.item WHERE name = :name AND serial = :serial",
                        name=ghost_item_name,
                        serial=ghost_serial,
                    )
                    cur.execute(q, {"name": ghost_item_name, "serial": ghost_serial})
                conn.commit()

    def test_no_orphans_or_ghosts(self, test_args, test_pool):
        """Verify clean database returns 0, 0."""
        with database.connect(test_args, pool=test_pool) as conn:
            orphan_count, ghost_count = startup._check_orphan_items(test_args, conn)

        assert orphan_count == 0, f"Expected 0 orphans, got {orphan_count}"
        assert ghost_count == 0, f"Expected 0 ghosts, got {ghost_count}"
