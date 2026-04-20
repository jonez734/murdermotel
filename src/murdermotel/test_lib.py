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


class TestLibQueries:
    def test_getitemcount(self, test_args, test_pool):
        from murdermotel import lib as libmm

        count = libmm.getitemcount(test_args, pool=test_pool)
        assert isinstance(count, int)
        assert count >= 0

    def test_getdefensecount(self, test_args, test_pool):
        from murdermotel import lib as libmm
        import psycopg

        try:
            count = libmm.getdefensecount(test_args, pool=test_pool)
        except psycopg.errors.UndefinedTable:
            pytest.skip("murdermotel.defense table does not exist")
        assert isinstance(count, int)
        assert count >= 0

    def test_getnpccount(self, test_args, test_pool):
        from murdermotel import lib as libmm

        count = libmm.getnpccount(test_args, pool=test_pool)
        assert isinstance(count, int)
        assert count >= 0

    def test_countdistributeditems(self, test_args, test_pool):
        from murdermotel import lib as libmm

        count = libmm.countdistributeditems(test_args, pool=test_pool)
        assert isinstance(count, int)
        assert count >= 0