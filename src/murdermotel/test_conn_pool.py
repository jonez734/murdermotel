"""Tests for conn/pool handling in database functions."""

import pytest

from bbsengine6 import database


class TestRoomConnPool:
    """Test room.load(), room.getitems(), room.getcount() with conn/pool."""

    def test_load_with_pool_only(self, test_args, test_pool, test_room):
        """Test room.load() works with pool passed directly."""
        from murdermotel import room as libroom

        result = libroom.load(test_args, test_room, pool=test_pool)
        assert result is not False
        assert result.id == test_room

    def test_load_with_conn_only(self, test_args, test_pool, test_room):
        """Test room.load() works with conn passed directly."""
        from murdermotel import room as libroom

        with database.connect(test_args, pool=test_pool) as conn:
            result = libroom.load(test_args, test_room, conn=conn)
            assert result is not False
            assert result.id == test_room

    def test_load_with_both_conn_and_pool(self, test_args, test_pool, test_room):
        """Test room.load() works with both conn and pool (conn takes priority)."""
        from murdermotel import room as libroom

        with database.connect(test_args, pool=test_pool) as conn:
            result = libroom.load(test_args, test_room, conn=conn, pool=test_pool)
            assert result is not False
            assert result.id == test_room

    def test_load_with_neither(self, test_args):
        """Test room.load() fails with neither conn nor pool."""
        from murdermotel import room as libroom

        result = libroom.load(test_args, 1, pool=None, conn=None)
        assert result is False

    def test_getitems_with_pool_only(self, test_args, test_pool, test_room, test_item_in_room):
        """Test room.getitems() works with pool passed directly."""
        from murdermotel import room as libroom

        items = libroom.getitems(test_args, test_room, pool=test_pool)
        assert isinstance(items, list)

    def test_getitems_with_conn_only(self, test_args, test_pool, test_room, test_item_in_room):
        """Test room.getitems() works with conn passed directly."""
        from murdermotel import room as libroom

        with database.connect(test_args, pool=test_pool) as conn:
            items = libroom.getitems(test_args, test_room, conn=conn)
            assert isinstance(items, list)

    def test_getitems_with_neither(self, test_args, test_room):
        """Test room.getitems() fails with neither conn nor pool."""
        from murdermotel import room as libroom

        items = libroom.getitems(test_args, test_room, pool=None, conn=None)
        assert items == []

    def test_getcount_with_pool_only(self, test_args, test_pool):
        """Test room.getcount() works with pool passed directly."""
        from murdermotel import room as libroom

        count = libroom.getcount(test_args, pool=test_pool)
        assert isinstance(count, int)
        assert count >= 0

    def test_getcount_with_conn_only(self, test_args, test_pool):
        """Test room.getcount() works with conn passed directly."""
        from murdermotel import room as libroom

        with database.connect(test_args, pool=test_pool) as conn:
            count = libroom.getcount(test_args, conn=conn)
            assert isinstance(count, int)
            assert count >= 0

    def test_getcount_with_neither(self, test_args):
        """Test room.getcount() fails with neither conn nor pool."""
        from murdermotel import room as libroom

        count = libroom.getcount(test_args, pool=None, conn=None)
        assert count == 0


class TestPlayerConnPool:
    """Test player functions with conn/pool."""

    def test_load_with_pool_only(self, test_args, test_pool, test_player):
        """Test player.load() works with pool passed directly."""
        from murdermotel import player

        p = player.load(test_args, test_player, pool=test_pool)
        assert p is not None
        assert p.moniker == test_player

    def test_load_with_conn_only(self, test_args, test_pool, test_player):
        """Test player.load() works with conn passed directly."""
        from murdermotel import player

        with database.connect(test_args, pool=test_pool) as conn:
            p = player.load(test_args, test_player, conn=conn)
            assert p is not None
            assert p.moniker == test_player

    def test_load_with_neither(self, test_args, test_player):
        """Test player.load() fails with neither conn nor pool."""
        from murdermotel import player

        p = player.load(test_args, test_player, pool=None, conn=None)
        assert p is None

    def test_getitems_with_pool_only(self, test_args, test_pool, test_player, test_item_on_player):
        """Test player.getitems() works with pool passed directly."""
        from murdermotel import player

        items = player.getitems(test_args, test_player, pool=test_pool)
        assert isinstance(items, list)

    def test_getitems_with_conn_only(self, test_args, test_pool, test_player, test_item_on_player):
        """Test player.getitems() works with conn passed directly."""
        from murdermotel import player

        with database.connect(test_args, pool=test_pool) as conn:
            items = player.getitems(test_args, test_player, conn=conn)
            assert isinstance(items, list)

    def test_getitems_with_neither(self, test_args, test_player):
        """Test player.getitems() fails with neither conn nor pool."""
        from murdermotel import player

        items = player.getitems(test_args, test_player, pool=None, conn=None)
        assert items == []

    def test_exists_with_pool_only(self, test_args, test_pool, test_player):
        """Test player.exists() works with pool passed directly."""
        from murdermotel import player

        exists = player.exists(test_args, test_player, pool=test_pool)
        assert exists is True

    def test_exists_with_conn_only(self, test_args, test_pool, test_player):
        """Test player.exists() works with conn passed directly."""
        from murdermotel import player

        with database.connect(test_args, pool=test_pool) as conn:
            exists = player.exists(test_args, test_player, conn=conn)
            assert exists is True

    def test_exists_with_neither(self, test_args, test_player):
        """Test player.exists() fails with neither conn nor pool."""
        from murdermotel import player

        exists = player.exists(test_args, test_player, pool=None, conn=None)
        assert exists is False


class TestItemConnPool:
    """Test item functions with conn/pool."""

    def test_load_with_pool_only(self, test_args, test_pool):
        """Test item.load() works with pool passed directly."""
        from murdermotel import item as libitem

        i = libitem.load(test_args, "knife", serial=1, pool=test_pool)
        assert i is not None

    def test_load_with_conn_only(self, test_args, test_pool):
        """Test item.load() works with conn passed directly."""
        from murdermotel import item as libitem

        with database.connect(test_args, pool=test_pool) as conn:
            i = libitem.load(test_args, "knife", serial=1, conn=conn)
            assert i is not None

    def test_load_with_neither(self, test_args):
        """Test item.load() fails with neither conn nor pool."""
        from murdermotel import item as libitem

        i = libitem.load(test_args, "knife", serial=1, pool=None, conn=None)
        assert i is None
