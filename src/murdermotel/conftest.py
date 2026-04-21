import argparse
import os
import pytest

from bbsengine6 import database


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
    TEST_PLAYER_MONIKER = "test_player_murdermotel"
    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query("""
                INSERT INTO $murdermotel.player (moniker, roomid, turn, moves, points, bodycount)
                VALUES (:moniker, 1, 1, 10, 0, 0)
                ON CONFLICT (moniker) DO UPDATE SET turn = excluded.turn
            """, moniker=TEST_PLAYER_MONIKER)
            cur.execute(q, {"moniker": TEST_PLAYER_MONIKER})
        conn.commit()

    yield TEST_PLAYER_MONIKER

    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query("DELETE FROM $murdermotel.player WHERE moniker = :moniker", moniker=TEST_PLAYER_MONIKER)
            cur.execute(q, {"moniker": TEST_PLAYER_MONIKER})
        conn.commit()