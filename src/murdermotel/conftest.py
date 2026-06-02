import argparse
import atexit
import os
import pytest
from unittest.mock import MagicMock

from bbsengine6 import database


_tracked_pools: list = []


def _cleanup_pools() -> None:
    import gc
    import threading
    import time

    try:
        database.reset_pool_cache()
    except Exception:
        pass

    for pool in list(_tracked_pools):
        try:
            pool.close()
        except Exception:
            pass

    _tracked_pools.clear()

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


atexit.register(_cleanup_pools)


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
    _tracked_pools.append(pool)
    yield pool
    _cleanup_pools()


@pytest.fixture(scope="session")
def test_player(test_args, test_pool):
    """Create a test player, yield moniker, then cleanup."""
    moniker = "test_player_murdermotel"
    try:
        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    """
                    INSERT INTO $murdermotel.player (moniker, roomid, turn, moves, points, bodycount)
                    VALUES (:moniker, 1, 1, 10, 0, 0)
                    ON CONFLICT (moniker) DO UPDATE SET turn = excluded.turn
                """,
                    moniker=moniker,
                )
                cur.execute(q, {"moniker": moniker})
            conn.commit()
        yield moniker
    except Exception:
        yield moniker


@pytest.fixture(scope="function")
def test_room(test_args, test_pool):
    """Create a test room, yield roomid, then cleanup."""
    room_id = 9999
    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                """
                INSERT INTO $murdermotel.playground 
                (id, shortname, title, description, north, south, east, west, up, down)
                VALUES (:id, 'test', 'Test Room', 'A test room', 0, 0, 0, 0, 0, 0)
                ON CONFLICT (id) DO NOTHING
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


@pytest.fixture(scope="function")
def test_item_in_room(test_args, test_pool, test_room):
    """Create a test item in a room, yield item dict, then cleanup."""
    item_name = "knife"
    item_serial = 1

    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                """
                INSERT INTO $murdermotel.map_item_room 
                (roomid, itemname, serial)
                VALUES (:roomid, :itemname, :serial)
                ON CONFLICT DO NOTHING
            """,
                roomid=test_room,
                itemname=item_name,
                serial=item_serial,
            )
            cur.execute(
                q, {"roomid": test_room, "itemname": item_name, "serial": item_serial}
            )
        conn.commit()

    yield {"roomid": test_room, "itemname": item_name, "serial": item_serial}

    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                "DELETE FROM $murdermotel.map_item_room WHERE roomid = :roomid AND itemname = :itemname AND serial = :serial",
                roomid=test_room,
                itemname=item_name,
                serial=item_serial,
            )
            cur.execute(
                q, {"roomid": test_room, "itemname": item_name, "serial": item_serial}
            )
        conn.commit()


@pytest.fixture(scope="function")
def mock_args():
    return MagicMock()


@pytest.fixture(scope="function")
def mock_pool():
    return MagicMock()


@pytest.fixture(scope="function")
def test_item_on_player(test_args, test_pool, test_player):
    """Create a test item on a player, yield item dict, then cleanup."""
    item_name = "knife"
    item_serial = 1

    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                """
                INSERT INTO $murdermotel.map_item_player 
                (playermoniker, itemname, serial)
                VALUES (:playermoniker, :itemname, :serial)
                ON CONFLICT DO NOTHING
            """,
                playermoniker=test_player,
                itemname=item_name,
                serial=item_serial,
            )
            cur.execute(
                q,
                {
                    "playermoniker": test_player,
                    "itemname": item_name,
                    "serial": item_serial,
                },
            )
        conn.commit()

    yield {"playermoniker": test_player, "itemname": item_name, "serial": item_serial}

    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            q = database.query(
                "DELETE FROM $murdermotel.map_item_player WHERE playermoniker = :playermoniker AND itemname = :itemname AND serial = :serial",
                playermoniker=test_player,
                itemname=item_name,
                serial=item_serial,
            )
            cur.execute(
                q,
                {
                    "playermoniker": test_player,
                    "itemname": item_name,
                    "serial": item_serial,
                },
            )
        conn.commit()


@pytest.fixture(scope="function")
def test_rooms(test_args, test_pool):
    """Create multiple test rooms, yield list of roomids, then cleanup."""
    room_ids = [50, 51, 52]

    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            for i, room_id in enumerate(room_ids):
                q = database.query(
                    """
                    INSERT INTO $murdermotel.playground
                    (id, shortname, title, description, north, south, east, west, up, down)
                    VALUES (:id, :shortname, :title, :description, :north, :south, :east, :west, :up, :down)
                    ON CONFLICT (id) DO UPDATE SET
                        shortname = EXCLUDED.shortname,
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        north = EXCLUDED.north,
                        south = EXCLUDED.south,
                        east = EXCLUDED.east,
                        west = EXCLUDED.west,
                        up = EXCLUDED.up,
                        down = EXCLUDED.down
                """,
                    id=room_id,
                    shortname=f"testroom{i}",
                    title=f"Test Room {i}",
                    description=f"Test description {i}",
                    north=room_ids[i + 1] if i < len(room_ids) - 1 else 0,
                    south=room_ids[i - 1] if i > 0 else 0,
                    east=0,
                    west=0,
                    up=0,
                    down=0,
                )
                cur.execute(
                    q,
                    {
                        "id": room_id,
                        "shortname": f"testroom{i}",
                        "title": f"Test Room {i}",
                        "description": f"Test description {i}",
                        "north": room_ids[i + 1] if i < len(room_ids) - 1 else 0,
                        "south": room_ids[i - 1] if i > 0 else 0,
                        "east": 0,
                        "west": 0,
                        "up": 0,
                        "down": 0,
                    },
                )
        conn.commit()

    yield room_ids

    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            for room_id in room_ids:
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
