"""Integration tests for the Z maintenance menu option.

Verifies that:
1. The 'W' (Weapon list) option appears in the Z menu
2. The W option calls the weaponlist module
3. Output is proper (recipes listed with component locations)
"""

from __future__ import annotations

from unittest.mock import patch


class TestZMenuWeaponList:
    def test_w_option_calls_weaponlist_module(
        self, test_args, test_pool, test_player, test_room
    ):
        from murdermotel import play as libplay

        with patch("murdermotel.play.io.inputchoice", return_value="W"):
            with patch("murdermotel.play.io.echo"):
                with patch("murdermotel.play.libmm.runsubmodule") as mock_run:
                    mock_run.return_value = True

                    room = type("Room", (), {"id": test_room})()
                    player = type("Player", (), {"moniker": test_player})()

                    result = libplay.maintmode(
                        test_args, player=player, room=room, pool=test_pool
                    )

                    mock_run.assert_called_once()
                    call_args = mock_run.call_args
                    args = call_args[0]
                    assert args[1] == "weaponlist"

    def test_q_option_returns_true(self, test_args, test_pool, test_player, test_room):
        from murdermotel import play as libplay

        with patch("murdermotel.play.io.inputchoice", return_value="Q"):
            with patch("murdermotel.play.io.echo"):
                room = type("Room", (), {"id": test_room})()
                player = type("Player", (), {"moniker": test_player})()

                result = libplay.maintmode(
                    test_args, player=player, room=room, pool=test_pool
                )
                assert result is True

    def test_z_menu_prompt_contains_w_option(
        self, test_args, test_pool, test_player, test_room
    ):
        from murdermotel import play as libplay

        with patch("murdermotel.play.io.inputchoice", return_value="Q"):
            with patch("murdermotel.play.io.echo"):
                room = type("Room", (), {"id": test_room})()
                player = type("Player", (), {"moniker": test_player})()

                libplay.maintmode(
                    test_args, player=player, room=room, pool=test_pool
                )

                mock_inputchoice = libplay.io.inputchoice
                mock_inputchoice.assert_called_once()
                call_args = mock_inputchoice.call_args
                prompt = call_args[0][0]
                assert "[W]" in prompt

    def test_weaponlist_recipes_shown(self, test_args, test_pool):
        from murdermotel import weaponlist as wl

        with patch("bbsengine6.io.echo") as mock_echo:
            result = wl._list_recipes(test_args, test_pool)
            assert result is True
            assert mock_echo.call_count >= 5
            echo_calls = [str(call) for call in mock_echo.call_args_list]
            output = "".join(echo_calls)
            assert "axe:" in output
            assert "pistol:" in output
            assert "chlorine:" in output
            assert "+" in output