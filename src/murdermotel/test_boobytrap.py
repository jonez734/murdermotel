class TestBoobyTrap:
    def test_access(self, test_args):
        from murdermotel import boobytrap as libbt

        assert libbt.access(test_args, "init") is True
        assert libbt.access(test_args, "run") is True
        assert libbt.access(test_args, "turn") is True
        assert libbt.access(test_args, "other") is False

    def test_init(self, test_args):
        from murdermotel import boobytrap as libbt

        result = libbt.init(test_args)
        assert result is True

    def test_buildargs(self, test_args):
        from murdermotel import boobytrap as libbt

        result = libbt.buildargs(test_args)
        assert result is None

    def test_main(self, test_args):
        from murdermotel import boobytrap as libbt

        result = libbt.main(test_args)
        assert result is True

    def test_load_no_pool(self, test_args):
        from murdermotel import boobytrap as libbt

        result = libbt.load(test_args, pool=None)
        assert result is None

    def test_save_no_pool(self, test_args):
        from murdermotel import boobytrap as libbt

        bt = libbt.build(test_args, {"name": "boobytrap", "running": False, "timer": 0})
        bt.roomid = 50
        result = libbt.save(test_args, bt, pool=None)
        assert result is False

    def test_create_no_pool(self, test_args):
        from murdermotel import boobytrap as libbt

        result = libbt.create(test_args, pool=None)
        assert result is False

    def test_exists_no_pool(self, test_args):
        from murdermotel import boobytrap as libbt

        result = libbt.exists(test_args, pool=None)
        assert result is False

    def test_get_room_no_pool(self, test_args):
        from murdermotel import boobytrap as libbt

        result = libbt.get_room_for_boobytrap(test_args, pool=None)
        assert result is None

    def test_build(self, test_args):
        from murdermotel import boobytrap as libbt

        b = libbt.build(
            test_args, {"name": "boobytrap", "running": True, "timer": 3}, roomid=50
        )
        assert b.name == "boobytrap"
        assert b.running is True
        assert b.timer == 3
        assert b.roomid == 50

    def test_buildrec(self, test_args):
        from murdermotel import boobytrap as libbt

        b = libbt.build(test_args, {"name": "boobytrap", "running": False, "timer": 0})
        rec = b.buildrec()
        assert rec["name"] == "boobytrap"
        assert rec["running"] is False
        assert rec["timer"] == 0

    def test_short(self, test_args):
        from murdermotel import boobytrap as libbt

        b = libbt.build(test_args, {"name": "boobytrap", "running": False, "timer": 0})
        assert b.short() == ":mousetrap: Booby-Trap"

    def test_turn_no_obj(self, test_args):
        from murdermotel import boobytrap as libbt

        result = libbt.turn(test_args, obj=None)
        assert result is False
