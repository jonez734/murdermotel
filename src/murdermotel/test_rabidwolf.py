class TestRabidWolf:
    def test_access(self, test_args):
        from murdermotel import rabidwolf as librw

        result = librw.access(test_args, "init")
        assert result is True

    def test_init(self, test_args):
        from murdermotel import rabidwolf as librw

        result = librw.init(test_args)
        assert result is True

    def test_buildargs(self, test_args):
        from murdermotel import rabidwolf as librw

        result = librw.buildargs(test_args)
        assert result is None

    def test_load_no_pool(self, test_args):
        from murdermotel import rabidwolf as librw

        result = librw.load(test_args, pool=None)
        assert result is None

    def test_create_no_pool(self, test_args):
        from murdermotel import rabidwolf as librw

        result = librw.create(test_args, pool=None)
        assert result is False

    def test_exists_no_pool(self, test_args):
        from murdermotel import rabidwolf as librw

        result = librw.exists(test_args, pool=None)
        assert result is False

    def test_build(self, test_args, test_pool):
        from murdermotel import rabidwolf as librw

        w = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 42, "healthpoints": 30},
            pool=test_pool,
        )
        assert w.name == "rabidwolf"
        assert w.roomid == 42
        assert w.healthpoints == 30

    def test_buildrec(self, test_args, test_pool):
        from murdermotel import rabidwolf as librw

        w = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 10, "healthpoints": 35},
            pool=test_pool,
        )
        rec = w.buildrec()
        assert rec["name"] == "rabidwolf"
        assert rec["roomid"] == 10
        assert rec["healthpoints"] == 35

    def test_short(self, test_args, test_pool):
        from murdermotel import rabidwolf as librw

        w = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 10, "healthpoints": 35},
            pool=test_pool,
        )
        assert w.short() == ":wolf: rabid wolf"

    def test_turn_no_player(self, test_args):
        from murdermotel import rabidwolf as librw

        result = librw.turn(test_args, obj=None)
        assert result is False

    def test_turn_no_obj(self, test_args):
        from murdermotel import rabidwolf as librw

        class FakePlayer:
            pass

        result = librw.turn(test_args, obj=None, player=FakePlayer())
        assert result is False

    def test_help_no_player(self, test_args):
        from murdermotel import rabidwolf as librw

        result = librw.help()
        assert result is False
