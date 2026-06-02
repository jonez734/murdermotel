"""Tests for weapon_recipe table and seed data."""

from bbsengine6 import database


class TestWeaponRecipe:
    def test_recipe_seed_data_loaded(self, test_args, test_pool):
        """weapon_recipe has expected rows after startup."""
        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    "SELECT name, component1, component2 FROM murdermotel.weapon_recipe ORDER BY name"
                )
                cur.execute(q)
                rows = cur.fetchall()

        names = [r["name"] for r in rows]
        assert "axe" in names, "axe recipe should exist"
        assert "pistol" in names, "pistol recipe should exist"
        assert "chlorine" in names, "chlorine recipe should exist"
        assert "fire" in names, "fire recipe should exist"
        assert "acid" in names, "acid recipe should exist"

        for row in rows:
            assert row["component1"], f"{row['name']}: component1 should not be empty"
            assert row["component2"], f"{row['name']}: component2 should not be empty"

    def test_recipe_state_is_valid_json(self, test_args, test_pool):
        """state column is valid JSON for all recipes."""
        import json

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query("SELECT name, state FROM murdermotel.weapon_recipe")
                cur.execute(q)
                rows = cur.fetchall()

        for row in rows:
            if row["state"] is not None:
                try:
                    json.loads(row["state"]) if isinstance(row["state"], str) else row[
                        "state"
                    ]
                except Exception as e:
                    raise AssertionError(f"{row['name']}: state is not valid JSON: {e}")

    def test_recipe_usemessages_not_empty(self, test_args, test_pool):
        """each recipe has at least one usemessages entry."""
        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    "SELECT name, usemessages FROM murdermotel.weapon_recipe"
                )
                cur.execute(q)
                rows = cur.fetchall()

        for row in rows:
            msgs = row["usemessages"]
            assert msgs is not None and len(msgs) > 0, (
                f"{row['name']}: should have at least one usemessages entry"
            )

    def test_weapons_handles_empty_recipe_table(self, test_args, test_pool):
        """Player.weapons() returns empty list when recipe list is empty."""
        from murdermotel import player as libplayer

        moniker = "test_player_empty_recipe"

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    """
                    INSERT INTO $murdermotel.player (moniker, roomid, turn, moves, points, bodycount)
                    VALUES (:moniker, 1, 1, 10, 0, 0)
                    ON CONFLICT (moniker) DO UPDATE SET turn = excluded.turn
                """,
                    moniker=moniker,
                )
                cur.execute(q, {"moniker": moniker})
            conn.commit()

        p = libplayer.load(test_args, moniker, pool=test_pool)
        if p is not None:
            p._weapon_recipes = []
            result = p.weapons()
            assert result == [], f"expected empty weapons list, got {result}"
