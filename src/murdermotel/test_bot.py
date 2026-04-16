import argparse
import os
import pytest

from bbsengine6 import database


TEST_LOGINID = "mm_test_user"
TEST_MEMBER_MONIKER = "test_member"


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
def test_engine_member(test_args, test_pool):
    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            cur.execute(
                """
                insert into engine.__member (moniker, email, loginid, tz, datecreated, credits)
                values (%s, %s, %s, %s, now(), 100)
                on conflict (moniker) do update set
                    loginid = excluded.loginid,
                    tz = excluded.tz
                """,
                (TEST_MEMBER_MONIKER, "test@murdermotel.local", TEST_LOGINID, "UTC"),
            )
        conn.commit()

    yield TEST_MEMBER_MONIKER

    with database.connect(test_args, pool=test_pool) as conn:
        with database.cursor(conn) as cur:
            cur.execute(
                "delete from engine.__member where moniker = %s",
                (TEST_MEMBER_MONIKER,),
            )
        conn.commit()


@pytest.fixture(scope="function")
def db_conn(test_args, test_pool, test_engine_member):
    conn = test_pool.getconn()
    conn.autocommit = False
    yield conn
    conn.rollback()
    test_pool.putconn(conn)


# ---------------------------------------------------------------------------
# Name generation
# ---------------------------------------------------------------------------

class TestBotNameGeneration:
    def test_bot_name_format(self):
        from murdermotel import bot
        name = bot.generate_bot_name()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_bot_name_pool_large_enough(self):
        # 25 prefixes * 25 suffixes = 625 possible unique names — well above BOT_MAX_COUNT
        from murdermotel import bot
        total = len(bot.BOT_PREFIXES) * len(bot.BOT_SUFFIXES)
        from murdermotel import lib as libmm
        assert total >= libmm.BOT_MAX_COUNT * 2

    def test_bot_name_is_prefix_plus_suffix(self):
        from murdermotel import bot
        # Generate many names and verify each one decomposes into a known prefix + suffix
        for _ in range(50):
            name = bot.generate_bot_name()
            matched = any(
                name.startswith(p) and name[len(p):] in bot.BOT_SUFFIXES
                for p in bot.BOT_PREFIXES
            )
            assert matched, f"Name {name!r} does not match any prefix+suffix pair"


# ---------------------------------------------------------------------------
# Mode distribution
# ---------------------------------------------------------------------------

class TestBotModeDistribution:
    def test_mode_distribution_less_than_5(self):
        from murdermotel import bot
        dist = bot.get_mode_distribution(3)
        assert dist["hybrid"] == 0.6
        assert dist["simple"] == 0.2
        assert dist["static"] == 0.1
        assert dist["full"] == 0.1

    def test_mode_distribution_5_to_10(self):
        from murdermotel import bot
        dist = bot.get_mode_distribution(7)
        assert dist["hybrid"] == 0.3
        assert dist["simple"] == 0.3
        assert dist["static"] == 0.2
        assert dist["full"] == 0.2

    def test_mode_distribution_more_than_10(self):
        from murdermotel import bot
        dist = bot.get_mode_distribution(15)
        assert dist["hybrid"] == 0.25
        assert dist["simple"] == 0.25
        assert dist["static"] == 0.25
        assert dist["full"] == 0.25

    def test_mode_distribution_sums_to_1(self):
        from murdermotel import bot
        for count in (1, 5, 10, 20):
            dist = bot.get_mode_distribution(count)
            assert abs(sum(dist.values()) - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# Experience score
# ---------------------------------------------------------------------------

class TestExperienceScore:
    def test_experience_score_basic(self):
        # Formula: (kills * 10) + points + (turns * 2)
        # (5 * 10) + 100 + (10 * 2) = 50 + 100 + 20 = 170
        from murdermotel import bot

        class MockEntity:
            bodycount = 5
            points = 100
            turn = 10

        score = bot.get_experience_score(MockEntity())
        assert score == 170

    def test_experience_score_zeros(self):
        from murdermotel import bot

        class MockEntity:
            bodycount = 0
            points = 0
            turn = 0

        assert bot.get_experience_score(MockEntity()) == 0

    def test_experience_score_missing_attributes(self):
        from murdermotel import bot
        # object() has no bodycount/points/turn — should default to 0
        assert bot.get_experience_score(object()) == 0

    def test_experience_score_kills_weighted_heaviest(self):
        from murdermotel import bot

        class KillHeavy:
            bodycount = 1
            points = 0
            turn = 0

        class PointsHeavy:
            bodycount = 0
            points = 9
            turn = 0

        # 1 kill = 10pts weight vs 9 points = 9pts weight
        assert bot.get_experience_score(KillHeavy()) > bot.get_experience_score(PointsHeavy())


# ---------------------------------------------------------------------------
# Weighted selection
# ---------------------------------------------------------------------------

class TestWeightedSelection:
    def test_weighted_select_returns_entity(self):
        from murdermotel import bot

        class E:
            def __init__(self, name, bodycount, points, turn):
                self.name = name
                self.bodycount = bodycount
                self.points = points
                self.turn = turn

        entities = [E("a", 0, 0, 0), E("b", 0, 0, 0), E("c", 0, 0, 0)]
        result = bot.weighted_select(entities)
        assert result in entities

    def test_weighted_select_single_entity(self):
        from murdermotel import bot

        class E:
            bodycount = 1
            points = 10
            turn = 5

        e = E()
        assert bot.weighted_select([e]) is e

    def test_weighted_select_empty_returns_none(self):
        from murdermotel import bot
        assert bot.weighted_select([]) is None

    def test_weighted_select_dominant_score_wins_often(self):
        # With a score 100x higher, the dominant entity should win nearly all the time
        from murdermotel import bot

        class E:
            def __init__(self, name, bodycount, points, turn):
                self.name = name
                self.bodycount = bodycount
                self.points = points
                self.turn = turn

        dominant = E("dominant", 100, 10000, 1000)
        weak = E("weak", 0, 0, 0)

        wins = sum(1 for _ in range(100) if bot.weighted_select([dominant, weak]) is dominant)
        # With all-zero score for weak, dominant should always win (100%)
        assert wins == 100


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestBotConstants:
    def test_bot_kill_points(self):
        from murdermotel import lib as libmm
        assert libmm.BOT_KILL_POINTS == 50

    def test_bot_max_count(self):
        from murdermotel import lib as libmm
        assert libmm.BOT_MAX_COUNT == 20

    def test_bot_modes(self):
        from murdermotel import lib as libmm
        assert libmm.BOT_MODE_STATIC == "static"
        assert libmm.BOT_MODE_SIMPLE == "simple"
        assert libmm.BOT_MODE_FULL == "full"
        assert libmm.BOT_MODE_HYBRID == "hybrid"

    def test_bot_mode_constants_exported_from_bot(self):
        from murdermotel import bot
        assert bot.BOT_MODE_STATIC == "static"
        assert bot.BOT_MODE_SIMPLE == "simple"
        assert bot.BOT_MODE_FULL == "full"
        assert bot.BOT_MODE_HYBRID == "hybrid"


# ---------------------------------------------------------------------------
# Bot class (no DB)
# ---------------------------------------------------------------------------

class TestBotClass:
    def test_bot_default_mode(self, test_args):
        from murdermotel import bot, lib as libmm
        b = bot.Bot(test_args, register=False)
        assert b.mode == libmm.BOT_MODE_HYBRID

    def test_bot_kind(self, test_args):
        from murdermotel import bot
        b = bot.Bot(test_args, register=False)
        assert b.kind == "bot"

    def test_bot_modulepath(self, test_args):
        from murdermotel import bot
        b = bot.Bot(test_args, register=False)
        assert b.modulepath == "bot"

    def test_bot_is_alive_default(self, test_args):
        from murdermotel import bot
        b = bot.Bot(test_args, register=False)
        assert b.is_alive is True

    def test_bot_short(self, test_args):
        from murdermotel import bot
        b = bot.Bot(test_args, name="GhostHunter", register=False)
        assert "GhostHunter" in b.short()

    def test_bot_all_modes_valid(self, test_args):
        from murdermotel import bot
        for mode in [bot.BOT_MODE_STATIC, bot.BOT_MODE_SIMPLE,
                     bot.BOT_MODE_FULL, bot.BOT_MODE_HYBRID]:
            b = bot.Bot(test_args, mode=mode, register=False)
            assert b.mode == mode

    def test_bot_buildrec_keys(self, test_args):
        from murdermotel import bot
        b = bot.Bot(test_args, name="TestBot", roomid=10, register=False)
        rec = b.buildrec()
        for key in ("name", "kind", "modulepath", "roomid", "is_bot",
                    "target", "targetedby", "is_alive", "state"):
            assert key in rec, f"Missing key {key!r} in buildrec()"
        assert rec["is_bot"] is True
        assert rec["state"]["mode"] == bot.BOT_MODE_HYBRID


# ---------------------------------------------------------------------------
# DB: persistence
# ---------------------------------------------------------------------------

class TestBotPersistence:
    def test_bot_save_load_core_fields(self, test_args, db_conn):
        from murdermotel import bot
        b = bot.Bot(test_args, name="SaveLoadBot", roomid=10,
                    mode="hybrid", register=False)
        b.is_alive = True
        b.target = "SomeTarget"
        b.targetedby = "SomeHunter"

        result = bot.save(test_args, b, conn=db_conn)
        assert result is True

        loaded = bot.load(test_args, "SaveLoadBot", conn=db_conn)
        assert loaded is not None
        assert loaded.name == "SaveLoadBot"
        assert loaded.roomid == 10
        assert loaded.mode == "hybrid"
        assert loaded.is_alive is True
        assert loaded.target == "SomeTarget"
        assert loaded.targetedby == "SomeHunter"

    def test_bot_save_idempotent(self, test_args, db_conn):
        # Saving twice should not raise
        from murdermotel import bot
        b = bot.Bot(test_args, name="IdempotentBot", roomid=10, register=False)
        assert bot.save(test_args, b, conn=db_conn) is True
        assert bot.save(test_args, b, conn=db_conn) is True


# ---------------------------------------------------------------------------
# DB: existence
# ---------------------------------------------------------------------------

class TestBotExistence:
    def test_bot_exists_true(self, test_args, db_conn):
        from murdermotel import bot
        b = bot.Bot(test_args, name="ExistsBot", roomid=10, register=False)
        bot.save(test_args, b, conn=db_conn)
        assert bot.exists(test_args, "ExistsBot", conn=db_conn) is True

    def test_bot_exists_false(self, test_args, db_conn):
        from murdermotel import bot
        assert bot.exists(test_args, "AbsolutelyNonExistentBot", conn=db_conn) is False


# ---------------------------------------------------------------------------
# DB: items
# ---------------------------------------------------------------------------

class TestBotItems:
    def test_bot_items_save_load(self, test_args, db_conn):
        from murdermotel import bot, item as libitem
        b = bot.Bot(test_args, name="ItemBot", roomid=10, register=False)
        bot.save(test_args, b, conn=db_conn)

        axe_blade = libitem.load(test_args, "axeblade", conn=db_conn)
        axe_handle = libitem.load(test_args, "axehandle", conn=db_conn)
        assert axe_blade is not None, "axeblade not found in test DB"
        assert axe_handle is not None, "axehandle not found in test DB"

        b.items = [axe_blade, axe_handle]
        bot.save(test_args, b, conn=db_conn)

        loaded = bot.load(test_args, "ItemBot", conn=db_conn)
        assert loaded is not None
        item_names = [i.name for i in loaded.items]
        assert "axeblade" in item_names
        assert "axehandle" in item_names

    def test_bot_items_cleared_on_save(self, test_args, db_conn):
        from murdermotel import bot, item as libitem
        b = bot.Bot(test_args, name="ItemClearBot", roomid=10, register=False)
        axe_blade = libitem.load(test_args, "axeblade", conn=db_conn)
        b.items = [axe_blade]
        bot.save(test_args, b, conn=db_conn)

        # Now clear items and re-save
        b.items = []
        bot.save(test_args, b, conn=db_conn)

        loaded = bot.load(test_args, "ItemClearBot", conn=db_conn)
        assert loaded.items == []


# ---------------------------------------------------------------------------
# DB: target assignment
# ---------------------------------------------------------------------------

class TestTargetAssignment:
    def test_assign_targets_bidirectional(self, test_args, db_conn):
        from murdermotel import bot

        # Insert two test players
        player_monikers = ["AssignPlayer1", "AssignPlayer2"]
        for moniker in player_monikers:
            with database.cursor(db_conn) as cur:
                cur.execute(
                    """INSERT INTO murdermotel.player
                       (moniker, roomid, turn, moves, membermoniker)
                       VALUES (%s, 10, 1, 60, %s)
                       ON CONFLICT (moniker) DO NOTHING""",
                    (moniker, TEST_MEMBER_MONIKER),
                )

        # Create two bots
        bots = []
        for i in range(2):
            b = bot.Bot(test_args, name=f"AssignBot{i}", roomid=10, register=False)
            bot.save(test_args, b, conn=db_conn)
            bots.append(b)

        bot.assign_targets(test_args, player_monikers, bots, conn=db_conn)

        # Each player should now have a target set
        for moniker in player_monikers:
            with database.cursor(db_conn) as cur:
                cur.execute(
                    "SELECT target FROM murdermotel.player WHERE moniker=%s",
                    (moniker,),
                )
                rec = cur.fetchone()
                assert rec is not None
                assert rec["target"] is not None, f"{moniker} has no target"

    def test_assign_targets_bot_gets_target(self, test_args, db_conn):
        from murdermotel import bot

        # One player, one bot
        with database.cursor(db_conn) as cur:
            cur.execute(
                """INSERT INTO murdermotel.player
                   (moniker, roomid, turn, moves, membermoniker)
                   VALUES (%s, 10, 1, 60, %s)
                   ON CONFLICT (moniker) DO NOTHING""",
                ("TargetPlayer", TEST_MEMBER_MONIKER),
            )

        b = bot.Bot(test_args, name="TargetedBot", roomid=10, register=False)
        bot.save(test_args, b, conn=db_conn)

        bot.assign_targets(test_args, ["TargetPlayer"], [b], conn=db_conn)

        # The bot should have a target too
        loaded = bot.load(test_args, "TargetedBot", conn=db_conn)
        assert loaded is not None
        assert loaded.target is not None


# ---------------------------------------------------------------------------
# DB: ensure_valid_target
# ---------------------------------------------------------------------------

class TestEnsureValidTarget:
    def test_ensure_valid_target_with_alive_target(self, test_args, db_conn):
        from murdermotel import bot
        # Create a living bot as the target
        target_bot = bot.Bot(test_args, name="AliveTarget", roomid=10, register=False)
        target_bot.is_alive = True
        bot.save(test_args, target_bot, conn=db_conn)

        hunter = bot.Bot(test_args, name="HunterBot", roomid=10, register=False)
        hunter.target = "AliveTarget"
        bot.save(test_args, hunter, conn=db_conn)

        result = bot.ensure_valid_target(test_args, hunter, conn=db_conn)
        assert result is True
        # Target should be unchanged
        assert hunter.target == "AliveTarget"

    def test_ensure_valid_target_with_dead_target(self, test_args, db_conn):
        from murdermotel import bot
        # Create a dead bot as the target
        dead_bot = bot.Bot(test_args, name="DeadTarget", roomid=10, register=False)
        dead_bot.is_alive = False
        bot.save(test_args, dead_bot, conn=db_conn)

        # Create a live bot to be reassigned to
        live_bot = bot.Bot(test_args, name="LiveReassign", roomid=10, register=False)
        live_bot.is_alive = True
        bot.save(test_args, live_bot, conn=db_conn)

        hunter = bot.Bot(test_args, name="ReassignHunter", roomid=10, register=False)
        hunter.target = "DeadTarget"
        bot.save(test_args, hunter, conn=db_conn)

        result = bot.ensure_valid_target(test_args, hunter, conn=db_conn)
        assert result is True
        # Target should have been reassigned away from the dead bot
        assert hunter.target != "DeadTarget"

    def test_ensure_valid_target_no_target(self, test_args, db_conn):
        from murdermotel import bot
        b = bot.Bot(test_args, name="NoTargetBot", roomid=10, register=False)
        b.target = None
        bot.save(test_args, b, conn=db_conn)

        result = bot.ensure_valid_target(test_args, b, conn=db_conn)
        assert result is True


# ---------------------------------------------------------------------------
# DB: get_alive_bots
# ---------------------------------------------------------------------------

class TestGetAliveBots:
    def test_get_alive_bots_returns_only_alive(self, test_args, db_conn):
        from murdermotel import bot
        alive = bot.Bot(test_args, name="AliveBot1", roomid=10, register=False)
        alive.is_alive = True
        bot.save(test_args, alive, conn=db_conn)

        dead = bot.Bot(test_args, name="DeadBot1", roomid=10, register=False)
        dead.is_alive = False
        bot.save(test_args, dead, conn=db_conn)

        alive_bots = bot.get_alive_bots(test_args, conn=db_conn)
        names = [b.name for b in alive_bots]
        assert "AliveBot1" in names
        assert "DeadBot1" not in names


# ---------------------------------------------------------------------------
# Kill points constant
# ---------------------------------------------------------------------------

class TestBotKillPoints:
    def test_bot_kill_points_constant(self):
        from murdermotel import lib as libmm
        assert libmm.BOT_KILL_POINTS == 50
