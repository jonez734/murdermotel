"""Tests for Player.weapons() recipe lookup from database."""

from bbsengine6 import database
from unittest.mock import MagicMock


class TestPlayerWeapons:
    def test_weapons_loads_recipes_from_db(self, test_args, test_pool):
        """_get_weapon_recipes queries weapon_recipe from database."""
        from murdermotel.player import _get_weapon_recipes

        with database.connect(test_args, pool=test_pool) as conn:
            recipes = _get_weapon_recipes(test_args, conn)

        assert len(recipes) > 0, "weapon_recipe should have entries"
        assert any(r["name"] == "axe" for r in recipes), "axe recipe should exist"

    def test_weapons_assembles_from_components(self):
        """Player weapons() assembles weapon from component items."""
        from murdermotel.player import Player

        mock_args = MagicMock()

        class FakeItem:
            def __init__(self, name):
                self.name = name

        p = Player(mock_args)
        p._weapon_recipes = [
            {"name": "axe", "c1": "axeblade", "c2": "axehandle"},
        ]
        p.items = [FakeItem("axeblade"), FakeItem("axehandle")]

        result = p.weapons()

        assert len(result) > 0, "should assemble weapon from matching components"
        assert "axe" in result[0].lower(), f"expected axe in result, got {result}"

    def test_weapons_missing_component_no_assembly(self):
        """Player weapons() does not assemble when a component is missing."""
        from murdermotel.player import Player

        mock_args = MagicMock()

        class FakeItem:
            def __init__(self, name):
                self.name = name

        p = Player(mock_args)
        p._weapon_recipes = [
            {"name": "axe", "c1": "axeblade", "c2": "axehandle"},
        ]
        p.items = [FakeItem("axeblade")]  # missing axehandle

        result = p.weapons()

        assert result == [], f"should not assemble with missing component, got {result}"

    def test_weapons_handles_multiple_recipes(self):
        """Player weapons() handles multiple recipes correctly."""
        from murdermotel.player import Player

        mock_args = MagicMock()

        class FakeItem:
            def __init__(self, name):
                self.name = name

        p = Player(mock_args)
        p._weapon_recipes = [
            {"name": "axe", "c1": "axeblade", "c2": "axehandle"},
            {"name": "pistol", "c1": "pistol", "c2": "bullets"},
        ]
        p.items = [
            FakeItem("axeblade"),
            FakeItem("axehandle"),
            FakeItem("pistol"),
            FakeItem("bullets"),
        ]

        result = p.weapons()

        assert len(result) == 2, f"should assemble 2 weapons, got {len(result)}"
        names = [w.replace(" (weapon)", "") for w in result]
        assert set(names) == {"axe", "pistol"}, f"expected axe and pistol, got {names}"

    def test_weapons_empty_recipes_returns_empty(self):
        """Player weapons() returns empty list when no recipes available."""
        from murdermotel.player import Player

        mock_args = MagicMock()

        class FakeItem:
            def __init__(self, name):
                self.name = name

        p = Player(mock_args)
        p._weapon_recipes = []
        p.items = [FakeItem("axeblade"), FakeItem("axehandle")]

        result = p.weapons()

        assert result == [], f"expected empty list, got {result}"

    def test_weapons_consumes_components_on_assembly(self):
        """Player weapons() removes components from the working copy, not self.items."""
        from murdermotel.player import Player

        mock_args = MagicMock()

        class FakeItem:
            def __init__(self, name):
                self.name = name

        p = Player(mock_args)
        p._weapon_recipes = [
            {"name": "axe", "c1": "axeblade", "c2": "axehandle"},
        ]
        p.items = [FakeItem("axeblade"), FakeItem("axehandle"), FakeItem("pistol")]

        items_before = len(p.items)
        result = p.weapons()

        assert len(result) > 0
        assert len(p.items) == items_before, (
            "weapons() operates on copy, not self.items"
        )
        assert "axe (weapon)" in result, "should assemble axe weapon"


class TestWeaponRecipeQueries:
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
