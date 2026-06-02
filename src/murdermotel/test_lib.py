from bbsengine6 import database
from unittest.mock import patch, MagicMock


class TestSetarea:
    @patch("murdermotel.lib.screen.setbottombar")
    def test_setarea_calls_screen_setbottombar(self, mock_sb, test_args, test_pool):
        from murdermotel import lib as libmm

        player = MagicMock()
        player.isdirty = False
        player.moniker = "TestPlayer"
        player.moves = 30
        player.turn = 2
        player.roomid = None

        libmm.setbottombar(test_args, "lobby", player=player, pool=test_pool)
        mock_sb.assert_called_once()
        call_args = mock_sb.call_args
        assert call_args.args[0] == "lobby"
        call_kwargs = call_args.kwargs
        assert call_kwargs["args"] is test_args
        assert call_kwargs["right"] is libmm._mm_game_state_fragment

    @patch("murdermotel.lib.screen.setbottombar")
    def test_setarea_passes_player_to_screen(self, mock_sb, test_args, test_pool):
        from murdermotel import lib as libmm

        player = MagicMock()
        player.isdirty = True
        player.moniker = "TestPlayer"
        player.moves = 30
        player.turn = 2
        player.roomid = None

        libmm.setbottombar(test_args, "playground", player=player, pool=test_pool)
        mock_sb.assert_called_once()
        call_kwargs = mock_sb.call_args.kwargs
        assert call_kwargs["player"] is player

    @patch("murdermotel.lib.screen.setbottombar")
    def test_setarea_custom_right_is_used(self, mock_sb, test_args, test_pool):
        from murdermotel import lib as libmm

        def custom(**kw) -> str:
            return "custom right"

        libmm.setbottombar(test_args, "lobby", right=custom, pool=test_pool)
        mock_sb.assert_called_once()
        assert mock_sb.call_args.kwargs["right"] is custom


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

    def test_getweaponrecipecount(self, test_args, test_pool):
        from murdermotel import lib as libmm

        count = libmm.getweaponrecipecount(test_args, pool=test_pool)
        assert isinstance(count, int)
        assert count >= 0

    def test_getweaponrecipecount_zero_on_empty(self, test_args, test_pool):
        from murdermotel import lib as libmm

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query("DELETE FROM murdermotel.weapon_recipe")
                cur.execute(q)
            conn.commit()

        count = libmm.getweaponrecipecount(test_args, pool=test_pool)
        assert count == 0, f"expected 0 on empty table, got {count}"

        with database.connect(test_args, pool=test_pool) as conn:
            database.importsql(
                test_args,
                "weapon_data.sql",
                conn=conn,
                package="murdermotel.data.sql",
            )

    def test_countdistributedweapons_zero(self, test_args, test_pool):
        from murdermotel import lib as libmm
        from bbsengine6 import database

        with database.connect(test_args, pool=test_pool) as conn:
            with database.cursor(conn) as cur:
                q = database.query(
                    "DELETE FROM murdermotel.map_item_room WHERE itemname IN (SELECT name FROM murdermotel.item WHERE kind = 'weapon')"
                )
                cur.execute(q)
                q = database.query("DELETE FROM murdermotel.item WHERE kind = 'weapon'")
                cur.execute(q)
            conn.commit()

        count = libmm.countdistributedweapons(test_args, pool=test_pool)
        assert count == 0, f"expected 0 with no weapons distributed, got {count}"

    def test_countdistributedweapons_after_distribution(
        self, test_args, test_pool, test_rooms
    ):
        from murdermotel import lib as libmm

        libmm.distributeweapons(test_args, weaponmode="complete", pool=test_pool)

        try:
            count = libmm.countdistributedweapons(test_args, pool=test_pool)
            assert count > 0, f"expected weapons after distribution, got {count}"
        finally:
            from bbsengine6 import database

            with database.connect(test_args, pool=test_pool) as conn:
                with database.cursor(conn) as cur:
                    q = database.query(
                        "DELETE FROM murdermotel.map_item_room WHERE itemname IN (SELECT name FROM murdermotel.item WHERE kind = 'weapon')"
                    )
                    cur.execute(q)
                    q = database.query(
                        "DELETE FROM murdermotel.item WHERE kind = 'weapon'"
                    )
                    cur.execute(q)
                conn.commit()
