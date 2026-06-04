"""Test that disabling the notify subsystem eliminates INTRANS warnings.

The notify module's count() function creates its own DB connections. When the
notify subsystem is disabled, count() returns 0 immediately without touching
the database, eliminating any potential INTRANS issues from the notify module.

Run with: python -m pytest test_no_intrans_warning.py -v -s
"""

from __future__ import annotations

import logging
import os

import pytest


_tracked_pools: list = []


def pytest_sessionfinish(session, exitstatus):
    import gc
    import threading
    import time

    for pool in list(_tracked_pools):
        try:
            pool.close()
        except Exception:
            pass
    _tracked_pools.clear()

    try:
        from bbsengine6 import database

        database.reset_pool_cache()
    except Exception:
        pass

    gc.collect()

    for _ in range(20):
        active_workers = sum(
            1
            for t in threading.enumerate()
            if t.name.startswith("psycopg") or t.name.startswith("pool-")
        )
        if active_workers == 0:
            break
        time.sleep(0.05)


@pytest.fixture(scope="session")
def test_args():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False)
    defaults = {
        "databasename": os.environ.get("MM_TEST_DBNAME", "zoid6test"),
        "databasehost": os.environ.get("MM_TEST_DBHOST", "/var/run/postgresql"),
        "databaseport": int(os.environ.get("MM_TEST_DBPORT", "5432")),
        "databaseuser": os.environ.get("MM_TEST_DBUSER", "opencode"),
        "databasepassword": os.environ.get("MM_TEST_DBPASS"),
    }
    from bbsengine6 import database

    database.buildargdatabasegroup(parser, defaults)
    args = parser.parse_args([])
    return args


@pytest.fixture(scope="session")
def test_pool(test_args):
    from bbsengine6 import database

    pool = database.getpool(test_args, dbname=test_args.databasename)
    test_args.pool = pool
    _tracked_pools.append(pool)
    yield pool


@pytest.fixture(scope="session")
def test_player(test_args, test_pool):
    from bbsengine6 import database

    moniker = "test_notify_intrans_player"
    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                """
                INSERT INTO $murdermotel.player (moniker, roomid, turn, moves, points, bodycount)
                VALUES (:moniker, 9999, 1, 10, 0, 0)
                ON CONFLICT (moniker) DO UPDATE SET
                    turn = excluded.turn,
                    moves = excluded.moves,
                    roomid = excluded.roomid
            """,
                moniker=moniker,
            )
            cur.execute(q, {"moniker": moniker})
        conn.commit()

    yield moniker

    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                "DELETE FROM $murdermotel.map_item_player WHERE playermoniker = :moniker",
                moniker=moniker,
            )
            cur.execute(q, {"moniker": moniker})
            q = database.query(
                "DELETE FROM $murdermotel.player WHERE moniker = :moniker",
                moniker=moniker,
            )
            cur.execute(q, {"moniker": moniker})
        conn.commit()


@pytest.fixture(scope="function")
def test_room(test_args, test_pool):
    from bbsengine6 import database

    room_id = 9999
    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                """
                INSERT INTO $murdermotel.playground
                (id, shortname, title, description, north, south, east, west, up, down)
                VALUES (:id, 'test', 'Test Room', 'A test room', 0, 0, 0, 0, 0, 0)
                ON CONFLICT (id) DO UPDATE SET
                    shortname = EXCLUDED.shortname,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description
            """,
                id=room_id,
            )
            cur.execute(q, {"id": room_id})
        conn.commit()

    yield room_id

    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                "DELETE FROM $murdermotel.map_item_room WHERE roomid = :roomid",
                roomid=room_id,
            )
            cur.execute(q, {"roomid": room_id})
            q = database.query(
                "DELETE FROM $murdermotel.playground WHERE id = :id",
                id=room_id,
            )
            cur.execute(q, {"id": room_id})
        conn.commit()


class TestNoIntransWarning:
    """Test that disabling notify eliminates INTRANS warnings."""

    def test_notify_count_disabled_returns_zero(self, test_args, test_pool, test_player):
        """Verify notify.count() returns 0 when disabled."""
        from bbsengine6 import notify

        moniker = test_player

        assert notify.is_enabled() is True
        notify.disable()
        assert notify.is_enabled() is False

        result = notify.count(moniker, args=test_args, pool=test_pool)
        assert result == 0

        notify.enable()

    def test_no_intrans_with_notify_disabled(self, test_args, test_pool, test_player, caplog):
        """Simulate lobby prompt path with notify disabled - no INTRANS warnings.

        This test exercises the get_notification_status() function which calls
        notify.count(). When notify is disabled, count() returns 0 immediately
        without acquiring a DB connection, so there should be no INTRANS warnings.
        """

        from bbsengine6 import notify
        from bbsengine6.io.screen import get_notification_status
        from bbsengine6.member import _threadlocal

        moniker = test_player
        _threadlocal.moniker = moniker

        with caplog.at_level(logging.WARNING):
            caplog.clear()

            notify.disable()

            try:
                result = get_notification_status(pool=test_pool)

                assert result == ""
                assert "INTRANS" not in caplog.text
                assert "rolling back" not in caplog.text
            finally:
                notify.enable()

    def test_lobby_prompt_path_no_intrans(self, test_args, test_pool, test_player, caplog):
        """Exercise the full lobby prompt path with notify disabled.

        This simulates what happens when displaying the lobby prompt:
        1. Set current moniker (creates DB connection)
        2. Call get_notification_status() (would call notify.count() if enabled)
        3. With notify disabled, no DB connections from notify module
        """

        from bbsengine6 import notify
        from bbsengine6.io.screen import get_notification_status
        from bbsengine6.member import _threadlocal

        moniker = test_player
        _threadlocal.moniker = moniker

        with caplog.at_level(logging.WARNING):
            caplog.clear()

            notify.disable()

            try:
                result = get_notification_status(pool=test_pool)

                assert result == ""
                assert "INTRANS" not in caplog.text

            finally:
                notify.enable()

    def test_notify_enabled_no_intrans(
        self, test_args, test_pool, test_player, caplog
    ):
        """Verify that with notify enabled and proper autocommit, no INTRANS warnings occur.

        The proper fix uses autocommit=True for read-only queries in notify.count().
        This eliminates INTRANS warnings without needing notify.disable().
        """

        from bbsengine6 import notify
        from bbsengine6.io.screen import get_notification_status
        from bbsengine6.member import _threadlocal

        moniker = test_player
        _threadlocal.moniker = moniker

        notify.enable()

        with caplog.at_level(logging.WARNING):
            caplog.clear()

            get_notification_status(pool=test_pool)

            intrans_count = caplog.text.count("INTRANS") + caplog.text.count(
                "rolling back"
            )
            print(f"\nWith notify enabled (fixed): {intrans_count} INTRANS warnings")
            print(f"Log output: {caplog.text}")

            assert intrans_count == 0, (
                "Expected NO INTRANS warnings with proper autocommit fix."
            )