import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_args():
    args = MagicMock()
    args.debug = False
    args.databasename = "zoid6test"
    args.databasehost = "/var/run/postgresql"
    args.databaseport = 5432
    args.databaseuser = "opencode"
    args.databasepassword = None
    return args


@pytest.fixture
def mock_pool():
    return MagicMock()


@pytest.fixture
def mock_conn(mock_pool):
    conn = MagicMock()
    mock_pool.getconn.return_value = conn
    return conn
