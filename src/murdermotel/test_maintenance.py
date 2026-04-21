class TestMaintenance:
    def test_weapons_count(self, test_args, test_pool):
        from murdermotel import maintenance as maint

        result = maint.weapons(test_args, pool=test_pool, items=None)
        assert result is False

    def test_access(self):
        from murdermotel import maintenance as maint

        result = maint.access(args=None, op="test")
        assert result is True

    def test_buildargs(self):
        from murdermotel import maintenance as maint

        result = maint.buildargs()
        assert result is None

    def test_init(self):
        from murdermotel import maintenance as maint

        result = maint.init()
        assert result is True
