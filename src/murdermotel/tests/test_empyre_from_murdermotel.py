"""Integration tests: murdermotel shell loads and runs with pool forwarding."""

from unittest.mock import patch

import pytest


class TestMurdermotelLobbyShell:
    """Test that pool flows through murdermotel lobby shell."""

    @patch("bbsengine6.io.echo")
    @patch("bbsengine6.module.runmodule")
    @patch("bbsengine6.io.inputchoice")
    @patch("bbsengine6.io.inputstring")
    @patch("bbsengine6.io.screen.setbottombar")
    @patch("bbsengine6.io.common.get_dsr")
    @patch("bbsengine6.member.getcurrentmoniker")
    @patch("murdermotel.bot.generate_bots")
    def test_pool_forwarded_to_startup(
        self,
        mock_generate_bots,
        mock_getmoniker,
        mock_get_dsr,
        mock_setbottombar,
        mock_inputstring,
        mock_inputchoice,
        mock_runmodule,
        mock_echo,
        mock_args,
        mock_pool,
    ):
        """Verify pool is passed to startup when lobby loads."""
        import murdermotel.lobby as mm_lobby

        mock_getmoniker.return_value = "TestPlayer"
        mock_get_dsr.return_value = (1, 1)
        mock_inputchoice.return_value = "Q"
        mock_runmodule.return_value = True
        mock_generate_bots.return_value = []

        mm_lobby.main(mock_args, pool=mock_pool)

        mock_runmodule.assert_called()
        call_args = mock_runmodule.call_args
        assert call_args.kwargs.get("pool") is mock_pool
        assert "startup" in call_args.args[1]

    @patch("bbsengine6.io.echo")
    @patch("bbsengine6.module.runmodule")
    @patch("bbsengine6.io.inputchoice")
    @patch("bbsengine6.io.inputstring")
    @patch("bbsengine6.io.screen.setbottombar")
    @patch("bbsengine6.io.common.get_dsr")
    @patch("bbsengine6.member.getcurrentmoniker")
    @patch("murdermotel.bot.generate_bots")
    def test_pool_none_propagates(
        self,
        mock_generate_bots,
        mock_getmoniker,
        mock_get_dsr,
        mock_setbottombar,
        mock_inputstring,
        mock_inputchoice,
        mock_runmodule,
        mock_echo,
        mock_args,
    ):
        """Verify pool=None is still passed (not silently fixed)."""
        import murdermotel.lobby as mm_lobby

        mock_getmoniker.return_value = "TestPlayer"
        mock_get_dsr.return_value = (1, 1)
        mock_inputchoice.return_value = "Q"
        mock_runmodule.return_value = True
        mock_generate_bots.return_value = []

        mm_lobby.main(mock_args, pool=None)

        mock_runmodule.assert_called()
        call_args = mock_runmodule.call_args
        assert call_args.kwargs.get("pool") is None
        assert "startup" in call_args.args[1]

    @patch("bbsengine6.io.echo")
    @patch("bbsengine6.module.runmodule")
    @patch("bbsengine6.io.inputchoice")
    @patch("bbsengine6.io.inputstring")
    @patch("bbsengine6.io.screen.setbottombar")
    @patch("bbsengine6.io.common.get_dsr")
    @patch("bbsengine6.member.getcurrentmoniker")
    @patch("murdermotel.bot.generate_bots")
    def test_startup_prg_passed(
        self,
        mock_generate_bots,
        mock_getmoniker,
        mock_get_dsr,
        mock_setbottombar,
        mock_inputstring,
        mock_inputchoice,
        mock_runmodule,
        mock_echo,
        mock_args,
        mock_pool,
    ):
        """Verify startup module is called with correct prg."""
        import murdermotel.lobby as mm_lobby

        mock_getmoniker.return_value = "TestPlayer"
        mock_get_dsr.return_value = (1, 1)
        mock_inputchoice.return_value = "Q"
        mock_runmodule.return_value = True
        mock_generate_bots.return_value = []

        mm_lobby.main(mock_args, pool=mock_pool)

        mock_runmodule.assert_called()
        call_args = mock_runmodule.call_args
        assert call_args.args[1] == "murdermotel.startup"


class TestMurdermotelLobbyPoolForwarding:
    """Test pool extraction and forwarding in murdermotel.lobby.main."""

    @patch("bbsengine6.io.echo")
    @patch("bbsengine6.module.runmodule")
    @patch("bbsengine6.io.inputchoice")
    @patch("bbsengine6.io.inputstring")
    @patch("bbsengine6.io.screen.setbottombar")
    @patch("bbsengine6.io.common.get_dsr")
    @patch("bbsengine6.member.getcurrentmoniker")
    @patch("murdermotel.bot.generate_bots")
    def test_startup_maintains_pool(
        self,
        mock_generate_bots,
        mock_getmoniker,
        mock_get_dsr,
        mock_setbottombar,
        mock_inputstring,
        mock_inputchoice,
        mock_runmodule,
        mock_echo,
        mock_args,
        mock_pool,
    ):
        """Simulate lobby session with pool maintained through startup."""
        import murdermotel.lobby as mm_lobby

        mock_getmoniker.return_value = "TestPlayer"
        mock_get_dsr.return_value = (1, 1)
        mock_inputchoice.return_value = "Q"
        mock_runmodule.return_value = True
        mock_generate_bots.return_value = []

        mm_lobby.main(mock_args, pool=mock_pool)

        assert mock_runmodule.call_count >= 1
        call_args = mock_runmodule.call_args
        assert call_args.kwargs.get("pool") is mock_pool

    @patch("bbsengine6.io.echo")
    @patch("bbsengine6.module.runmodule")
    @patch("bbsengine6.io.inputchoice")
    @patch("bbsengine6.io.inputstring")
    @patch("bbsengine6.io.screen.setbottombar")
    @patch("bbsengine6.io.common.get_dsr")
    @patch("bbsengine6.member.getcurrentmoniker")
    @patch("murdermotel.bot.generate_bots")
    def test_multiple_lobby_calls_maintain_pool(
        self,
        mock_generate_bots,
        mock_getmoniker,
        mock_get_dsr,
        mock_setbottombar,
        mock_inputstring,
        mock_inputchoice,
        mock_runmodule,
        mock_echo,
        mock_args,
        mock_pool,
    ):
        """Verify pool is correctly forwarded through all lobby operations."""
        import murdermotel.lobby as mm_lobby

        mock_getmoniker.return_value = "TestPlayer"
        mock_get_dsr.return_value = (1, 1)
        mock_inputchoice.return_value = "Q"
        mock_runmodule.return_value = True
        mock_generate_bots.return_value = []

        mm_lobby.main(mock_args, pool=mock_pool)

        for call in mock_runmodule.call_args_list:
            if call.args and "startup" in call.args[1]:
                assert call.kwargs.get("pool") is mock_pool


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
