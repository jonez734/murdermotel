"""Integration tests: murdermotel.main() forwards pool to lobby."""

from unittest.mock import MagicMock, patch

import pytest


class TestMurdermotelMainPoolForwarding:
    """Test that murdermotel.main() properly forwards pool to lobby."""

    @patch("bbsengine6.module.run")
    def test_main_forwards_pool_to_lobby(
        self,
        mock_run,
        mock_args,
        mock_pool,
    ):
        """Verify murdermotel.main() forwards pool to murdermotel.lobby."""
        import murdermotel

        mock_run.return_value = True

        result = murdermotel.main(mock_args, pool=mock_pool)

        assert result is None
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args.args[1] == "murdermotel.lobby"
        assert call_args.kwargs.get("pool") is mock_pool

    @patch("bbsengine6.module.run")
    def test_main_creates_pool_if_none(
        self,
        mock_run,
        mock_args,
    ):
        """Verify murdermotel.main() creates pool if not provided."""
        import murdermotel

        mock_run.return_value = True

        mock_new_pool = MagicMock()
        mock_new_pool.__enter__ = MagicMock(return_value=mock_new_pool)
        mock_new_pool.__exit__ = MagicMock(return_value=False)

        with patch("bbsengine6.database.getpool", return_value=mock_new_pool):
            result = murdermotel.main(mock_args, pool=None)

        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
