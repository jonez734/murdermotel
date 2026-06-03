"""Tests for weapon recipe completion.

Verifies that when a player has both components of a recipe,
weapons() returns the weapon name with components consumed from the working copy.
"""

from __future__ import annotations


class TestWeaponRecipeCompletion:
    def test_weapons_completes_recipe_consumes_components(self):
        """Player weapons() completes recipe, consumes components, returns weapon name."""
        from murdermotel.player import Player
        from unittest.mock import MagicMock

        mock_args = MagicMock()

        class FakeItem:
            def __init__(self, name):
                self.name = name

        p = Player(mock_args)
        p._weapon_recipes = [
            {"name": "acid", "c1": "industrialacid", "c2": "acidsprayer"},
        ]
        p.items = [FakeItem("industrialacid"), FakeItem("acidsprayer"), FakeItem("sword")]

        items_before = len(p.items)

        result = p.weapons()

        assert "acid (weapon)" in result, f"Expected 'acid (weapon)' in result, got: {result}"
        assert len(p.items) == items_before, (
            f"weapons() should not modify self.items. Expected {items_before}, got {len(p.items)}"
        )

    def test_weapons_partial_components_no_weapon(self):
        """Player weapons() returns empty when only one component present."""
        from murdermotel.player import Player
        from unittest.mock import MagicMock

        mock_args = MagicMock()

        class FakeItem:
            def __init__(self, name):
                self.name = name

        p = Player(mock_args)
        p._weapon_recipes = [
            {"name": "acid", "c1": "industrialacid", "c2": "acidsprayer"},
        ]
        p.items = [FakeItem("industrialacid")]

        result = p.weapons()

        assert result == [], f"Expected empty list with missing component, got: {result}"

    def test_weapons_both_components_required(self):
        """Player weapons() requires both component1 and component2."""
        from murdermotel.player import Player
        from unittest.mock import MagicMock

        mock_args = MagicMock()

        class FakeItem:
            def __init__(self, name):
                self.name = name

        p = Player(mock_args)
        p._weapon_recipes = [
            {"name": "acid", "c1": "industrialacid", "c2": "acidsprayer"},
        ]
        p.items = [FakeItem("acidsprayer")]

        result = p.weapons()

        assert result == [], f"Missing component1, expected empty, got: {result}"

    def test_weapons_handles_multiple_recipes(self):
        """Player weapons() completes multiple recipes when all components present."""
        from murdermotel.player import Player
        from unittest.mock import MagicMock

        mock_args = MagicMock()

        class FakeItem:
            def __init__(self, name):
                self.name = name

        p = Player(mock_args)
        p._weapon_recipes = [
            {"name": "acid", "c1": "industrialacid", "c2": "acidsprayer"},
            {"name": "axe", "c1": "axeblade", "c2": "axehandle"},
        ]
        p.items = [
            FakeItem("industrialacid"),
            FakeItem("acidsprayer"),
            FakeItem("axeblade"),
            FakeItem("axehandle"),
        ]

        result = p.weapons()

        assert len(result) == 2, f"Expected 2 weapons, got: {result}"
        assert "acid (weapon)" in result, "Expected 'acid (weapon)' in result"
        assert "axe (weapon)" in result, "Expected 'axe (weapon)' in result"