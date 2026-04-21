class TestLibQueries:
    def test_getitemcount(self, test_args, test_pool):
        from murdermotel import lib as libmm

        count = libmm.getitemcount(test_args, pool=test_pool)
        assert isinstance(count, int)
        assert count >= 0

    def test_getdefensecount(self, test_args, test_pool):
        from murdermotel import lib as libmm

        count = libmm.getdefensecount(test_args, pool=test_pool)
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
