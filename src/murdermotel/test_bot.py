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


class TestBotQueries:
    def test_get_player_count(self, test_args, test_pool):
        from murdermotel import bot

        count = bot.get_player_count(test_args, pool=test_pool)
        assert isinstance(count, int)
        assert count >= 0

    def test_get_alive_bots(self, test_args, test_pool):
        from murdermotel import bot

        bots = bot.get_alive_bots(test_args, pool=test_pool)
        assert isinstance(bots, list)