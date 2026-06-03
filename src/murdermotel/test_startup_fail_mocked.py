"""Tests for startup.py failure scenarios using mocking."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_args():
    """Create mock args for startup."""
    args = MagicMock()
    args.debug = False
    args.databasename = "murdermotel"
    args.databasehost = "/var/run/postgresql"
    args.databaseport = 5432
    args.databaseuser = "opencode"
    args.databasepassword = None
    args.pool = None
    return args


class TestStartupFailMocked:
    """Test startup.py failure scenarios by mocking database functions."""

    @patch("bbsengine6.database.schemaexists")
    @patch("bbsengine6.database.createschema")
    def test_schema_creation_fails(
        self, mock_createschema, mock_schemaexists, mock_args
    ):
        """Verify startup fails when schema creation fails."""
        from murdermotel import startup

        mock_schemaexists.return_value = False
        mock_createschema.return_value = False

        with patch("bbsengine6.database.connect", autospec=True) as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_connect.return_value.__exit__.return_value = False

            result = startup.main(mock_args, conn=mock_conn)

        assert result is False, "Startup should fail when schema creation fails"

    @patch("bbsengine6.database.schemaexists")
    @patch("bbsengine6.database.createschema")
    @patch("bbsengine6.database.classexists")
    @patch("bbsengine6.database.importsql")
    def test_table_import_fails(
        self,
        mock_importsql,
        mock_classexists,
        mock_createschema,
        mock_schemaexists,
        mock_args,
    ):
        """Verify startup fails when table import fails."""
        from murdermotel import startup

        mock_schemaexists.return_value = True
        mock_createschema.return_value = True
        mock_classexists.return_value = False
        mock_importsql.return_value = False

        with patch("bbsengine6.database.connect", autospec=True) as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_connect.return_value.__exit__.return_value = False

            result = startup.main(mock_args, conn=mock_conn)

        assert result is False, "Startup should fail when table import fails"

    @patch("bbsengine6.database.schemaexists")
    @patch("bbsengine6.database.createschema")
    @patch("bbsengine6.database.classexists")
    @patch("bbsengine6.database.importsql")
    @patch("bbsengine6.database.manage_schema_priv")
    def test_privilege_grant_fails(
        self,
        mock_manage_priv,
        mock_importsql,
        mock_classexists,
        mock_createschema,
        mock_schemaexists,
        mock_args,
    ):
        """Verify startup fails when privilege grant fails."""
        from murdermotel import startup

        mock_schemaexists.return_value = True
        mock_createschema.return_value = True
        mock_classexists.return_value = True
        mock_importsql.return_value = True
        mock_manage_priv.return_value = False

        with patch("bbsengine6.database.connect", autospec=True) as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_connect.return_value.__exit__.return_value = False

            result = startup.main(mock_args, conn=mock_conn)

        assert result is False, "Startup should fail when privilege grant fails"


class TestStartupMainIntegration:
    """Integration-style tests that patch more thoroughly."""

    @patch("murdermotel.startup._check_orphan_items")
    @patch("murdermotel.startup._populate_rooms")
    @patch("murdermotel.lib.distributeitems")
    @patch("bbsengine6.database.schemaexists")
    @patch("bbsengine6.database.createschema")
    @patch("bbsengine6.database.classexists")
    @patch("bbsengine6.database.importsql")
    @patch("bbsengine6.database.manage_schema_priv")
    def test_item_distribution_fails(
        self,
        mock_manage_priv,
        mock_importsql,
        mock_classexists,
        mock_createschema,
        mock_schemaexists,
        mock_distribute,
        mock_populate,
        mock_check,
        mock_args,
    ):
        """Verify startup fails when item distribution fails."""
        from murdermotel import startup

        mock_schemaexists.return_value = True
        mock_createschema.return_value = True
        mock_classexists.return_value = True
        mock_importsql.return_value = True
        mock_manage_priv.return_value = True
        mock_check.return_value = (0, 0)
        mock_populate.return_value = True
        mock_distribute.return_value = False

        with patch("bbsengine6.database.connect", autospec=True) as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.rowcount = 0
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value.__exit__.return_value = False
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_connect.return_value.__exit__.return_value = False

            result = startup.main(mock_args, conn=mock_conn)

        assert result is False, "Startup should fail when item distribution fails"

    @patch("murdermotel.startup._check_orphan_items")
    @patch("murdermotel.startup._populate_rooms")
    @patch("murdermotel.lib.distributeitems")
    @patch("bbsengine6.database.schemaexists")
    @patch("bbsengine6.database.createschema")
    @patch("bbsengine6.database.classexists")
    @patch("bbsengine6.database.importsql")
    @patch("bbsengine6.database.manage_schema_priv")
    def test_populate_rooms_fails(
        self,
        mock_manage_priv,
        mock_importsql,
        mock_classexists,
        mock_createschema,
        mock_schemaexists,
        mock_distribute,
        mock_populate,
        mock_check,
        mock_args,
    ):
        """Verify startup fails when room population fails."""
        from murdermotel import startup

        mock_schemaexists.return_value = True
        mock_createschema.return_value = True
        mock_classexists.return_value = True
        mock_importsql.return_value = True
        mock_manage_priv.return_value = True
        mock_check.return_value = (0, 0)
        mock_populate.return_value = False
        mock_distribute.return_value = True

        with patch("bbsengine6.database.connect", autospec=True) as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.rowcount = 0
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value.__exit__.return_value = False
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_connect.return_value.__exit__.return_value = False

            result = startup.main(mock_args, conn=mock_conn)

        assert result is False, "Startup should fail when room population fails"


class TestStartupDatabaseErrors:
    """Test various database error scenarios."""

    @patch("bbsengine6.database.schemaexists")
    @patch("bbsengine6.database.createschema")
    @patch("bbsengine6.database.classexists")
    @patch("bbsengine6.database.importsql")
    @patch("bbsengine6.database.manage_schema_priv")
    @patch("murdermotel.startup._check_orphan_items")
    @patch("murdermotel.room.getcount")
    @patch("murdermotel.lib.getitemcount")
    @patch("murdermotel.lib.getdefensecount")
    @patch("murdermotel.lib.countdistributeditems")
    @patch("murdermotel.lib.getnpccount")
    @patch("bbsengine6.database.connect")
    def test_npc_import_fails(
        self,
        mock_connect,
        mock_getnpccount,
        mock_dist_count,
        mock_def_count,
        mock_item_count,
        mock_room_count,
        mock_check,
        mock_manage_priv,
        mock_importsql,
        mock_classexists,
        mock_createschema,
        mock_schemaexists,
        mock_args,
    ):
        """Verify startup fails when NPC import fails."""
        from murdermotel import startup

        mock_schemaexists.return_value = True
        mock_createschema.return_value = True
        mock_classexists.side_effect = [True] * 9 + [False]
        mock_importsql.side_effect = [True] * 8 + [False]
        mock_manage_priv.return_value = True
        mock_check.return_value = (0, 0)
        mock_room_count.return_value = 10
        mock_item_count.return_value = 0
        mock_def_count.return_value = 0
        mock_dist_count.return_value = 0
        mock_getnpccount.return_value = 0

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = False

        result = startup.main(mock_args, conn=mock_conn)

        assert result is False, "Startup should fail when NPC import fails"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
