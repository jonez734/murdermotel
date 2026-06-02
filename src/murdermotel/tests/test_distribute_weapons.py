"""Tests for distributeweapons() function in lib.py"""


from bbsengine6 import database


class TestDistributeWeapons:
    def test_components_mode_noop(self, test_args, test_pool):
        """distributeweapons() returns True immediately for components mode."""
        from murdermotel import lib as libmm

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    "DELETE FROM murdermotel.map_item_room WHERE itemname IN (SELECT name FROM murdermotel.item WHERE kind = 'weapon')"
                )
                cur.execute(q)
                q = database.query("DELETE FROM murdermotel.item WHERE kind = 'weapon'")
                cur.execute(q)
            conn.commit()

        result = libmm.distributeweapons(
            test_args, weaponmode="components", pool=test_pool
        )

        assert result is True

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    "SELECT COUNT(*) AS count FROM murdermotel.item WHERE kind = 'weapon'"
                )
                cur.execute(q)
                count = cur.fetchone()["count"]

        assert count == 0, "components mode should not create any weapon items"

    def test_complete_mode_generates_weapons(self, test_args, test_pool, test_rooms):
        """distributeweapons() generates kind='weapon' items in complete mode."""
        from murdermotel import lib as libmm

        try:
            result = libmm.distributeweapons(
                test_args, weaponmode="complete", pool=test_pool
            )

            assert result is True

            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "SELECT COUNT(*) AS count FROM murdermotel.item WHERE kind = 'weapon'"
                    )
                    cur.execute(q)
                    weapon_count = cur.fetchone()["count"]

                    q = database.query(
                        "SELECT COUNT(*) AS count FROM murdermotel.map_item_room AS m "
                        "JOIN murdermotel.item AS i ON i.name = m.itemname AND i.serial = m.serial "
                        "WHERE i.kind = 'weapon'"
                    )
                    cur.execute(q)
                    placed_count = cur.fetchone()["count"]

            assert weapon_count > 0, "should generate weapon items in item table"
            assert placed_count > 0, "should place weapon items in rooms"
        finally:
            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM murdermotel.map_item_room WHERE itemname IN (SELECT name FROM murdermotel.item WHERE kind = 'weapon')"
                    )
                    cur.execute(q)
                    q = database.query(
                        "DELETE FROM murdermotel.item WHERE kind = 'weapon'"
                    )
                    cur.execute(q)
                conn.commit()

    def test_both_mode_generates_weapons(self, test_args, test_pool, test_rooms):
        """distributeweapons() generates weapons in 'both' mode."""
        from murdermotel import lib as libmm

        try:
            result = libmm.distributeweapons(
                test_args, weaponmode="both", pool=test_pool
            )

            assert result is True

            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "SELECT COUNT(*) AS count FROM murdermotel.item WHERE kind = 'weapon'"
                    )
                    cur.execute(q)
                    count = cur.fetchone()["count"]

            assert count > 0, "both mode should generate weapon items"
        finally:
            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM murdermotel.map_item_room WHERE itemname IN (SELECT name FROM murdermotel.item WHERE kind = 'weapon')"
                    )
                    cur.execute(q)
                    q = database.query(
                        "DELETE FROM murdermotel.item WHERE kind = 'weapon'"
                    )
                    cur.execute(q)
                conn.commit()

    def test_zero_count_disabled(self, test_args, test_pool):
        """Recipes with count=0 generate no instances."""
        from murdermotel import lib as libmm

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    "DELETE FROM murdermotel.weapon_recipe WHERE name = 'axe'"
                )
                cur.execute(q)
                q = database.query(
                    "INSERT INTO murdermotel.weapon_recipe (name, component1, component2, count) "
                    "VALUES ('axe', 'axeblade', 'axehandle', 0)"
                )
                cur.execute(q)
            conn.commit()

        try:
            result = libmm.distributeweapons(
                test_args, weaponmode="complete", pool=test_pool
            )

            assert result is True

            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "SELECT COUNT(*) AS count FROM murdermotel.item "
                        "WHERE kind = 'weapon' AND name = 'axe'"
                    )
                    cur.execute(q)
                    count = cur.fetchone()["count"]

            assert count == 0, "count=0 should generate no instances"
        finally:
            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM murdermotel.item WHERE name = 'axe' AND kind = 'weapon'"
                    )
                    cur.execute(q)
                    q = database.query(
                        "DELETE FROM murdermotel.map_item_room WHERE itemname = 'axe'"
                    )
                    cur.execute(q)
                    q = database.query(
                        "DELETE FROM murdermotel.weapon_recipe WHERE name = 'axe'"
                    )
                    cur.execute(q)
                    q = database.query(
                        "INSERT INTO murdermotel.weapon_recipe (name, title, component1, component2, count, usemessages, state) "
                        "VALUES ('axe', 'Axe', 'axeblade', 'axehandle', 6, "
                        "array['You swing the axe with all your might and slaughter', "
                        "'THUCK! WHACK! THUCK! You hack away and finish', 'You butcher'], "
                        '\'{"damage_min": 15, "damage_max": 30, "type": "melee", "power": "high"}\')'
                    )
                    cur.execute(q)
                conn.commit()

    def test_max_three_per_room(self, test_args, test_pool, test_rooms):
        """No room receives more than 3 weapon instances."""
        from murdermotel import lib as libmm

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    "DELETE FROM murdermotel.map_item_room WHERE itemname IN (SELECT name FROM murdermotel.item WHERE kind = 'weapon')"
                )
                cur.execute(q)
                q = database.query("DELETE FROM murdermotel.item WHERE kind = 'weapon'")
                cur.execute(q)
            conn.commit()

        try:
            result = libmm.distributeweapons(
                test_args, weaponmode="complete", pool=test_pool
            )

            assert result is True

            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "SELECT roomid, COUNT(*) AS cnt FROM murdermotel.map_item_room AS m "
                        "JOIN murdermotel.item AS i ON i.name = m.itemname AND i.serial = m.serial "
                        "WHERE i.kind = 'weapon' "
                        "GROUP BY roomid HAVING COUNT(*) > 3"
                    )
                    cur.execute(q)
                    over_limit = cur.fetchall()

            assert len(over_limit) == 0, f"rooms over 3 weapon limit: {over_limit}"
        finally:
            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM murdermotel.map_item_room WHERE itemname IN (SELECT name FROM murdermotel.item WHERE kind = 'weapon')"
                    )
                    cur.execute(q)
                    q = database.query(
                        "DELETE FROM murdermotel.item WHERE kind = 'weapon'"
                    )
                    cur.execute(q)
                conn.commit()

    def test_no_duplicate_weapon_names_per_room(self, test_args, test_pool):
        """The same weapon name does not appear twice in the same room."""
        from murdermotel import lib as libmm

        try:
            result = libmm.distributeweapons(
                test_args, weaponmode="complete", pool=test_pool
            )

            assert result is True

            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "SELECT roomid, itemname, COUNT(*) AS cnt FROM murdermotel.map_item_room AS m "
                        "JOIN murdermotel.item AS i ON i.name = m.itemname AND i.serial = m.serial "
                        "WHERE i.kind = 'weapon' "
                        "GROUP BY roomid, itemname HAVING COUNT(*) > 1"
                    )
                    cur.execute(q)
                    duplicates = cur.fetchall()

            assert len(duplicates) == 0, (
                f"duplicate weapon names per room: {duplicates}"
            )
        finally:
            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM murdermotel.map_item_room WHERE itemname IN (SELECT name FROM murdermotel.item WHERE kind = 'weapon')"
                    )
                    cur.execute(q)
                    q = database.query(
                        "DELETE FROM murdermotel.item WHERE kind = 'weapon'"
                    )
                    cur.execute(q)
                conn.commit()
