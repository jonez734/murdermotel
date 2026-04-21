import pytest


class TestThief:
    def test_access(self, test_args):
        from murdermotel import thief as libthief

        assert libthief.access(test_args, "init") is True
        assert libthief.access(test_args, "run") is True
        assert libthief.access(test_args, "turn") is True
        assert libthief.access(test_args, "other") is False

    def test_init(self, test_args):
        from murdermotel import thief as libthief

        result = libthief.init(test_args)
        assert result is True

    def test_buildargs(self, test_args):
        from murdermotel import thief as libthief

        result = libthief.buildargs(test_args)
        assert result is None

    def test_main(self, test_args):
        from murdermotel import thief as libthief

        result = libthief.main(test_args)
        assert result is True

    def test_load_no_pool(self, test_args):
        from murdermotel import thief as libthief

        result = libthief.load(test_args, pool=None)
        assert result is None

    def test_save_no_pool(self, test_args):
        from murdermotel import thief as libthief

        result = libthief.save(test_args, None, pool=None)
        assert result is False

    def test_create_no_pool(self, test_args):
        from murdermotel import thief as libthief

        result = libthief.create(test_args, pool=None)
        assert result is False

    def test_getitems_no_pool(self, test_args):
        from murdermotel import thief as libthief

        result = libthief.getitems(test_args, pool=None)
        assert result == []

    def test_exists_no_pool(self, test_args):
        from murdermotel import thief as libthief

        result = libthief.exists(test_args, pool=None)
        assert result is False

    def test_build(self, test_args, test_pool):
        from murdermotel import thief as libthief

        t = libthief.build(
            test_args,
            {"name": "thief", "bag": ["knife"], "roomid": 42, "healthpoints": 30},
            pool=test_pool,
        )
        assert t.name == "thief"
        assert t.bag == ["knife"]
        assert t.roomid == 42
        assert t.healthpoints == 30

    def test_buildrec(self, test_args, test_pool):
        from murdermotel import thief as libthief

        t = libthief.build(
            test_args,
            {"name": "thief", "bag": [], "roomid": 10, "healthpoints": 35},
            pool=test_pool,
        )
        t.bag = ["knife"]
        rec = t.buildrec()
        assert rec["name"] == "thief"
        assert rec["bag"] == ["knife"]
        assert rec["roomid"] == 10

    def test_short(self, test_args, test_pool):
        from murdermotel import thief as libthief

        t = libthief.build(
            test_args,
            {"name": "thief", "bag": [], "roomid": 10, "healthpoints": 35},
            pool=test_pool,
        )
        assert t.short() == ":supervillian: Thief"

    def test_turn_no_player(self, test_args):
        from murdermotel import thief as libthief

        result = libthief.turn(test_args, obj=None)
        assert result is False

    def test_steal_from_player_empty(self, test_args):
        from murdermotel import thief as libthief

        class FakePlayer:
            items = []

        result = libthief.steal_from_player(FakePlayer(), None)
        assert result is None
