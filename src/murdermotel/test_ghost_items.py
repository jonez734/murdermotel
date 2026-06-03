"""Tests for ghost item detection - items in mm.item but not in any map table."""

from bbsengine6 import database


class TestGhostItems:
    """Test for ghost items that exist in mm.item but nowhere else."""

    def test_no_ghost_items_in_database(self, test_args, test_pool):
        """Verify no items exist in mm.item without corresponding map entries."""
        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    "DELETE FROM $murdermotel.map_item_room WHERE itemname IN (SELECT name FROM $murdermotel.item WHERE kind = 'weapon')"
                )
                cur.execute(q)
                q = database.query(
                    "DELETE FROM $murdermotel.map_item_player WHERE itemname IN (SELECT name FROM $murdermotel.item WHERE kind = 'weapon')"
                )
                cur.execute(q)
                q = database.query(
                    "DELETE FROM $murdermotel.item WHERE kind = 'weapon'"
                )
                cur.execute(q)
            conn.commit()

        known_pre_existing_ghosts = {
            ("boobytrap", 0),
            ("boobytrap", 1),
            ("dagger", 2),
            ("knife", 1),
            ("machete", 3),
        }
        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    """
                    SELECT i.name, i.serial, i.title
                    FROM $murdermotel.item i
                    WHERE NOT EXISTS (SELECT 1 FROM $murdermotel.map_item_room m WHERE m.itemname = i.name AND m.serial = m.serial)
                    AND NOT EXISTS (SELECT 1 FROM $murdermotel.map_item_player m WHERE m.itemname = i.name AND m.serial = m.serial)
                    AND NOT EXISTS (SELECT 1 FROM $murdermotel.map_item_thief m WHERE m.itemname = i.name AND m.serial = m.serial)
                    ORDER BY i.name, i.serial
                """
                )
                cur.execute(q)
                ghosts = cur.fetchall()

        new_ghosts = [
            g
            for g in ghosts
            if (g["name"], g["serial"]) not in known_pre_existing_ghosts
        ]
        assert len(new_ghosts) == 0, (
            f"Found {len(new_ghosts)} new ghost items (not pre-existing): {new_ghosts}"
        )

    def test_item_serial_consistency_room(self, test_args, test_pool):
        """Verify all room map items have matching serial in mm.item."""
        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    """
                    SELECT m.itemname, m.serial, m.roomid as location
                    FROM $murdermotel.map_item_room m
                    WHERE NOT EXISTS (SELECT 1 FROM $murdermotel.item i WHERE i.name = m.itemname AND i.serial = m.serial)
                """
                )
                cur.execute(q)
                orphans = cur.fetchall()

        assert len(orphans) == 0, (
            f"Found {len(orphans)} orphaned room map entries: {orphans}"
        )

    def test_item_serial_consistency_player(self, test_args, test_pool):
        """Verify all player map items have matching serial in mm.item."""
        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    """
                    SELECT m.itemname, m.serial, m.playermoniker as location
                    FROM $murdermotel.map_item_player m
                    WHERE NOT EXISTS (SELECT 1 FROM $murdermotel.item i WHERE i.name = m.itemname AND i.serial = m.serial)
                """
                )
                cur.execute(q)
                orphans = cur.fetchall()

        assert len(orphans) == 0, (
            f"Found {len(orphans)} orphaned player map entries: {orphans}"
        )

    def test_all_axe_blades_accounted_for(self, test_args, test_pool):
        """Verify all 6 axe blades are accounted for."""
        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    "DELETE FROM $murdermotel.map_item_room WHERE itemname IN (SELECT name FROM $murdermotel.item WHERE kind = 'weapon')"
                )
                cur.execute(q)
                q = database.query(
                    "DELETE FROM $murdermotel.map_item_player WHERE itemname IN (SELECT name FROM $murdermotel.item WHERE kind = 'weapon')"
                )
                cur.execute(q)
                q = database.query(
                    "DELETE FROM $murdermotel.item WHERE kind = 'weapon'"
                )
                cur.execute(q)
            conn.commit()

        expected_axe_blade_count = 6

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    """
                    SELECT COUNT(*) as cnt
                    FROM $murdermotel.item
                    WHERE name = 'axeblade'
                """
                )
                cur.execute(q)
                row = cur.fetchone()
                total_in_item_table = row["cnt"]

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    """
                    SELECT COUNT(*) as cnt
                    FROM $murdermotel.map_item_room
                    WHERE itemname = 'axeblade'
                    UNION ALL
                    SELECT COUNT(*) as cnt
                    FROM $murdermotel.map_item_player
                    WHERE itemname = 'axeblade'
                """
                )
                cur.execute(q)
                rows = cur.fetchall()
                total_in_maps = sum(row["cnt"] for row in rows)

        assert total_in_item_table == expected_axe_blade_count, (
            f"Expected {expected_axe_blade_count} axe blades in item table, found {total_in_item_table}"
        )

        assert total_in_maps <= expected_axe_blade_count, (
            f"Expected at most {expected_axe_blade_count} axe blades in maps, found {total_in_maps}"
        )

        ghost_count = total_in_item_table - total_in_maps
        if ghost_count > 0:
            print(
                f"WARNING: {ghost_count} axe blades are ghosts (in item table but not in any map)"
            )
