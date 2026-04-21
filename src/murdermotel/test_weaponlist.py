import pytest


class TestWeaponlist:
    def test_init(self):
        from murdermotel import weaponlist as wl

        result = wl.init()
        assert result is True

    def test_access(self, test_args):
        from murdermotel import weaponlist as wl

        result = wl.access(test_args, op="test")
        assert result in (True, False, None)

    def test_buildargs(self, test_args):
        from murdermotel import weaponlist as wl

        result = wl.buildargs(test_args)
        assert result is None

    def test_main_no_pool(self, test_args):
        from murdermotel import weaponlist as wl

        result = wl.main(test_args)
        assert result is False
