import argparse
import os
import pytest

from bbsengine6 import database


TEST_PLAYER_MONIKER = "test_player_murdermotel"


@pytest.fixture(scope="session")
def test_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False)
    defaults = {
        "databasename": os.environ.get("MM_TEST_DBNAME", "zoid6test"),
        "databasehost": os.environ.get("MM_TEST_DBHOST", "/var/run/postgresql"),
        "databaseport": int(os.environ.get("MM_TEST_DBPORT", "5432")),
        "databaseuser": os.environ.get("MM_TEST_DBUSER", "opencode"),
        "databasepassword": os.environ.get("MM_TEST_DBPASS"),
    }
    database.buildargdatabasegroup(parser, defaults)
    args = parser.parse_args([])
    return args


@pytest.fixture(scope="session")
def test_pool(test_args):
    pool = database.getpool(test_args, dbname=test_args.databasename)
    test_args.pool = pool
    yield pool
    pool.close()


@pytest.fixture(scope="session")
def test_player(test_args, test_pool):
    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            cur.execute(
                "INSERT INTO murdermotel.player (moniker, roomid, turn, moves, points, bodycount) "
                "VALUES (%s, 1, 1, 10, 0, 0) "
                "ON CONFLICT (moniker) DO UPDATE SET turn = excluded.turn",
                (TEST_PLAYER_MONIKER,),
            )
        conn.commit()

    yield TEST_PLAYER_MONIKER

    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            cur.execute("DELETE FROM murdermotel.player WHERE moniker = %s", (TEST_PLAYER_MONIKER,))
        conn.commit()


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
                cur.execute(
                    "INSERT INTO engine.__member (moniker, email, loginid, tz, datecreated, credits) "
                    "VALUES (%s, %s, %s, %s, now(), 100) "
                    "ON CONFLICT (moniker) DO UPDATE SET email = excluded.email",
                    (moniker_str, "test@test.local", moniker_str, "UTC"),
                )
                cur.execute("UPDATE murdermotel.player SET membermoniker = %s WHERE moniker = %s", (moniker_str, moniker_str))
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