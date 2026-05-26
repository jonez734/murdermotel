"""Integration tests: murdermotel can be invoked via various entry points."""

import subprocess
import sys

import pytest


class TestMurdermotelRunMethods:
    """Test different entry points to run murdermotel."""

    def test_runs_via_python_m_dash_m_flag(self):
        """Verify murdermotel runs via python -m murdermotel --help."""
        result = subprocess.run(
            [sys.executable, "-m", "murdermotel", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout
        assert "murdermotel" in result.stdout

    def test_runs_via_module_entry_point(self):
        """Verify murdermotel runs when invoked as a module."""
        result = subprocess.run(
            [sys.executable, "-c", "import murdermotel; print('ok')"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "ok" in result.stdout

    def test_main_function_exists(self):
        """Verify murdermotel.__main__.main() is callable."""
        from murdermotel import __main__

        assert hasattr(__main__, "main")
        assert callable(__main__.main)

    def test_main_accepts_no_args(self):
        """Verify murdermotel.__main__.main() doesn't require args."""
        from murdermotel import __main__

        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--debug", action="store_true", default=False)

        args = parser.parse_args([])
        args.databasename = "zoid6test"
        args.databasehost = "/var/run/postgresql"
        args.databaseport = 5432
        args.databaseuser = "opencode"
        args.databasepassword = None

        from unittest.mock import patch

        with patch("bbsengine6.io.echo"):
            try:
                __main__.main()
            except SystemExit:
                pass

    def test_bin_script_runs_via_subprocess(self):
        """Verify bin/murdermotel can be executed via subprocess."""
        import os

        bin_path = (
            "/home/opencode/data/work/murdermotel/src/murdermotel/bin/murdermotel"
        )
        if os.path.exists(bin_path):
            result = subprocess.run(
                [sys.executable, bin_path, "--help"],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert "usage:" in result.stdout
            assert "murdermotel" in result.stdout


class TestMurdermotelImports:
    """Test that murdermotel can be imported as a module."""

    def test_import_murdermotel_package(self):
        """Verify murdermotel package can be imported."""
        import murdermotel

        assert murdermotel is not None

    def test_import_lib_module(self):
        """Verify murdermotel.lib can be imported."""
        from murdermotel import lib

        assert lib is not None
        assert hasattr(lib, "SCHEMA")
        assert lib.SCHEMA == "murdermotel"

    def test_import_lobby_module(self):
        """Verify murdermotel.lobby can be imported."""
        from murdermotel import lobby

        assert lobby is not None
        assert hasattr(lobby, "main")

    def test_import_startup_module(self):
        """Verify murdermotel.startup can be imported."""
        from murdermotel import startup

        assert startup is not None
        assert hasattr(startup, "main")

    def test_lib_runmodule_exists(self):
        """Verify murdermotel.lib.runmodule exists and is callable."""
        from murdermotel import lib

        assert hasattr(lib, "runmodule")
        assert callable(lib.runmodule)

    def test_lib_buildargs_exists(self):
        """Verify murdermotel.lib.buildargs exists and is callable."""
        from murdermotel import lib

        assert hasattr(lib, "buildargs")
        assert callable(lib.buildargs)


class TestMurdermotelPackageInfo:
    """Test murdermotel package metadata and version info."""

    def test_package_version_from__version_module(self):
        """Verify murdermotel._version exists and has version info."""
        from murdermotel import _version

        assert _version is not None
        assert hasattr(_version, "githash") or hasattr(_version, "__version__")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
