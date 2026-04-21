import argparse
import os
import pytest

from bbsengine6 import database


TEST_PLAYER_MONIKER = "test_player_murdermotel"


@pytest.fixture(scope="function")
def db_conn(test_args, test_pool, test_player):
    conn = test_pool.getconn()
    conn.autocommit = False
    yield conn
    conn.rollback()
    test_pool.putconn(conn)


class TestPlayerQueries:
    def test_player_load(self, test_args, test_pool, test_player):
        from murdermotel import player

        p = player.load(test_args, test_player, pool=test_pool)
        assert p is not None
        assert p.moniker == test_player

    def test_player_exists_true(self, test_args, test_pool, test_player):
        from murdermotel import player

        exists = player.exists(test_args, test_player, pool=test_pool)
        assert exists is True

    def test_player_exists_false(self, test_args, test_pool):
        from murdermotel import player

        exists = player.exists(test_args, "nonexistent_player_xyz", pool=test_pool)
        assert exists is False

    def test_player_count(self, test_args, test_pool, test_player):
        from murdermotel import player
        from bbsengine6 import member

        moniker_str = test_player
        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                moniker_str = test_player
                q = database.query("""
                    INSERT INTO $engine.__member (moniker, email, loginid, tz, datecreated, credits)
                    VALUES (:moniker, :email, :loginid, :tz, now(), 100)
                    ON CONFLICT (moniker) DO UPDATE SET email = excluded.email
                """, moniker=moniker_str, email="test@test.local", loginid=moniker_str, tz="UTC")
                cur.execute(q, {"moniker": moniker_str, "email": "test@test.local", "loginid": moniker_str, "tz": "UTC"})
                q = database.query("UPDATE $murdermotel.player SET membermoniker = :membermoniker WHERE moniker = :moniker", membermoniker=moniker_str, moniker=moniker_str)
                cur.execute(q, {"membermoniker": moniker_str, "moniker": moniker_str})
            conn.commit()
        count = player.count(test_args, moniker_str, pool=test_pool)
        assert count >= 1

    def test_query_function_basic(self, test_args, test_pool, test_player):
        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                moniker_str = test_player
                q = database.query("SELECT * FROM $murdermotel.player WHERE moniker = :moniker", moniker=moniker_str)
                cur.execute(q, {"moniker": moniker_str})
                rec = cur.fetchone()
                assert rec is not None
                assert rec["moniker"] == moniker_str

    def test_query_function_positional(self, test_args, test_pool, test_player):
        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                moniker_str = test_player
                q = database.query("SELECT moniker FROM $murdermotel.player WHERE moniker = :moniker", moniker=moniker_str)
                cur.execute(q, {"moniker": moniker_str})
                rec = cur.fetchone()
                assert rec is not None
                assert rec["moniker"] == moniker_str

    def test_query_function_no_params(self, test_args, test_pool, test_player):
        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                moniker_str = test_player
                q = database.query("SELECT moniker FROM $murdermotel.player WHERE moniker = :moniker", moniker=moniker_str)
                cur.execute(q, {"moniker": moniker_str})
                rec = cur.fetchone()
                assert rec is not None