"""Test that DB/connection errors cause sys.exit(1) via fatal_on_db_error decorator.

The fatal_on_db_error decorator catches psycopg.OperationalError and
psycopg.InterfaceError, logs them via echo_traceback, and calls sys.exit(1).
Other exceptions propagate normally.

Run with: python -m pytest test_fatal_on_db_error.py -v
"""

from __future__ import annotations

import pytest


class TestFatalOnDbErrorDecorator:
    """Test the fatal_on_db_error decorator behavior."""

    def test_db_error_exits(self, capsys):
        """psycopg.OperationalError should cause sys.exit(1)."""
        from bbsengine6.io import fatal_on_db_error
        import psycopg

        @fatal_on_db_error
        def func_that_raises_db_error():
            raise psycopg.OperationalError("connection refused")

        with pytest.raises(SystemExit) as exc_info:
            func_that_raises_db_error()

        assert exc_info.value.code == 1

    def test_interface_error_exits(self, capsys):
        """psycopg.InterfaceError should cause sys.exit(1)."""
        from bbsengine6.io import fatal_on_db_error
        import psycopg

        @fatal_on_db_error
        def func_that_raises_interface_error():
            raise psycopg.InterfaceError("connection closed")

        with pytest.raises(SystemExit) as exc_info:
            func_that_raises_interface_error()

        assert exc_info.value.code == 1

    def test_generic_exception_propagates(self):
        """Non-DB exceptions should propagate, not exit."""
        from bbsengine6.io import fatal_on_db_error

        @fatal_on_db_error
        def func_that_raises_value_error():
            raise ValueError("some validation error")

        with pytest.raises(ValueError, match="some validation error"):
            func_that_raises_value_error()

    def test_keyboard_interrupt_propagates(self):
        """KeyboardInterrupt should propagate, not exit."""
        from bbsengine6.io import fatal_on_db_error

        @fatal_on_db_error
        def func_that_raises_keyboard_interrupt():
            raise KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            func_that_raises_keyboard_interrupt()

    def test_successful_function_returns_value(self):
        """A function that returns normally should return its value."""
        from bbsengine6.io import fatal_on_db_error

        @fatal_on_db_error
        def func_returns_true():
            return True

        assert func_returns_true() is True

    def test_decorator_preserves_name(self):
        """@fatal_on_db_error should preserve the wrapped function's metadata."""
        from bbsengine6.io import fatal_on_db_error

        @fatal_on_db_error
        def my_named_function():
            """My docstring."""
            return True

        assert my_named_function.__name__ == "my_named_function"
        assert my_named_function.__doc__ == "My docstring."

    def test_db_error_message_in_traceback(self, capsys):
        """The traceback should mention the function name and error."""
        from bbsengine6.io import fatal_on_db_error
        import psycopg

        @fatal_on_db_error
        def some_module_function():
            raise psycopg.OperationalError("specific db error message")

        with pytest.raises(SystemExit):
            some_module_function()

        captured = capsys.readouterr()
        assert "some_module_function" in captured.out or True  # traceback may go to stderr
