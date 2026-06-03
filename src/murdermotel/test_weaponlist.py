"""Tests for weaponlist module."""

from unittest.mock import patch



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

    def test_list_recipes_shows_output(self, test_args, test_pool):
        from murdermotel import weaponlist as wl

        with patch("bbsengine6.io.echo") as mock_echo:
            result = wl._list_recipes(test_args, test_pool)
            assert result is True
            assert mock_echo.call_count >= 5
            echo_args = [str(call) for call in mock_echo.call_args_list]
            output = "".join(echo_args)
            assert "axe:" in output
            assert "pistol:" in output
            assert "chlorine:" in output
            assert "+" in output

    def test_main_recipes_option(self, test_args, test_pool):
        from murdermotel import weaponlist as wl

        with patch("murdermotel.weaponlist.io.inputchar", side_effect=["R", "Q"]):
            with patch("murdermotel.weaponlist.io.echo"):
                result = wl.main(test_args, pool=test_pool)
                assert result is True

    def test_main_quit(self, test_args, test_pool):
        from murdermotel import weaponlist as wl

        with patch("murdermotel.weaponlist.io.inputchar", return_value="Q"):
            result = wl.main(test_args, pool=test_pool)
            assert result is True

    def test_main_components_option(self, test_args, test_pool):
        from murdermotel import weaponlist as wl

        with patch("murdermotel.weaponlist.io.inputchar", side_effect=["C", "Q"]):
            with patch("murdermotel.weaponlist.io.echo") as mock_echo:
                result = wl.main(test_args, pool=test_pool)
                assert result is True
                assert mock_echo.call_count > 0
