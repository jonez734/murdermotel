from unittest.mock import MagicMock, patch

from murdermotel import lib as _  # noqa: F401 - Must import first to avoid circular import
from murdermotel import rabidwolf as librw


class TestWolfAttackPlayer:
    def test_wolf_attack_reduces_player_moves(self, test_args, test_pool):
        player = MagicMock()
        player.moves = 100
        player.save = MagicMock()

        wolf = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 1, "healthpoints": 35},
            pool=test_pool,
        )

        with patch("murdermotel.rabidwolf.io.echo"):
            with patch("murdermotel.rabidwolf.util.diceroll", return_value=1):
                librw.wolf_attack_player(test_args, wolf, player=player)

        assert player.moves < 100
        player.save.assert_called_once()

    def test_wolf_attack_deals_11_to_20_damage(self, test_args, test_pool):
        player = MagicMock()
        player.moves = 100
        player.save = MagicMock()

        wolf = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 1, "healthpoints": 35},
            pool=test_pool,
        )

        with patch("murdermotel.rabidwolf.io.echo"):
            with patch("murdermotel.rabidwolf.randomlib.randint", return_value=5):
                librw.wolf_attack_player(test_args, wolf, player=player)

        assert player.moves == 85

    def test_wolf_kills_player(self, test_args, test_pool):
        player = MagicMock()
        player.moves = 15
        player.save = MagicMock()

        wolf = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 1, "healthpoints": 35},
            pool=test_pool,
        )

        with patch("murdermotel.rabidwolf.io.echo") as mock_echo:
            with patch("murdermotel.rabidwolf.randomlib.randint", return_value=10):
                librw.wolf_attack_player(test_args, wolf, player=player)

        assert player.moves == 0
        dead_messages = [
            str(call)
            for call in mock_echo.call_args_list
            if "dead" in str(call).lower()
        ]
        assert len(dead_messages) > 0


class TestPlayerAttackWolf:
    def test_attack_kills_wolf(self, test_args, test_pool):
        player = MagicMock()
        player.moves = 50
        player.name = "testplayer"
        player.save = MagicMock()

        wolf = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 1, "healthpoints": 20},
            pool=test_pool,
        )

        with patch("murdermotel.rabidwolf.io.echo"):
            with patch("murdermotel.rabidwolf.util.diceroll", return_value=6):
                librw.attack(test_args, player, ["knife"], wolf)

        assert wolf.roomid == 0
        assert wolf.healthpoints == 0
        assert player.moves == 555

    def test_attack_damages_wolf_not_killed(self, test_args, test_pool):
        player = MagicMock()
        player.moves = 50
        player.name = "testplayer"
        player.save = MagicMock()

        wolf = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 1, "healthpoints": 35},
            pool=test_pool,
        )

        with patch("murdermotel.rabidwolf.io.echo"):
            with patch("murdermotel.rabidwolf.util.diceroll", return_value=1):
                librw.attack(test_args, player, ["knife"], wolf)

        assert wolf.healthpoints == 30
        assert wolf.roomid == 1

    def test_attack_deals_5_to_30_damage(self, test_args, test_pool):
        player = MagicMock()
        player.moves = 50
        player.name = "testplayer"
        player.save = MagicMock()

        wolf = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 1, "healthpoints": 35},
            pool=test_pool,
        )

        for roll, expected_damage in [(1, 5), (3, 15), (6, 30)]:
            wolf.healthpoints = 35
            with patch("murdermotel.rabidwolf.io.echo"):
                with patch("murdermotel.rabidwolf.util.diceroll", return_value=roll):
                    librw.attack(test_args, player, ["knife"], wolf)
            assert wolf.healthpoints == 35 - expected_damage

    def test_attack_gains_moves(self, test_args, test_pool):
        player = MagicMock()
        player.moves = 50
        player.name = "testplayer"
        player.save = MagicMock()

        wolf = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 1, "healthpoints": 35},
            pool=test_pool,
        )

        with patch("murdermotel.rabidwolf.io.echo"):
            with patch("murdermotel.rabidwolf.util.diceroll", return_value=1):
                librw.attack(test_args, player, ["knife"], wolf)

        assert player.moves == 55


class TestTurnCombat:
    def test_turn_retaliates_when_attacked(self, test_args, test_pool):
        player = MagicMock()
        player.moves = 100
        player.roomid = 1
        player.save = MagicMock()

        wolf = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 1, "healthpoints": 35},
            pool=test_pool,
        )

        with patch("murdermotel.rabidwolf.io.echo"):
            with patch("murdermotel.rabidwolf.util.diceroll", return_value=1):
                with patch("murdermotel.rabidwolf.randomlib.randint", return_value=5):
                    result = librw.turn(
                        test_args, obj=wolf, player=player, attacked=True
                    )

        assert result is True
        assert player.moves < 100

    def test_turn_no_retaliation_above_threshold(self, test_args, test_pool):
        player = MagicMock()
        player.moves = 100
        player.roomid = 1
        player.save = MagicMock()

        wolf = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 1, "healthpoints": 35},
            pool=test_pool,
        )

        with patch("murdermotel.rabidwolf.io.echo") as mock_echo:
            with patch("murdermotel.rabidwolf.util.diceroll", return_value=7):
                result = librw.turn(test_args, obj=wolf, player=player, attacked=True)

        assert result is True
        attack_calls = [
            str(call) for call in mock_echo.call_args_list if "claws" in str(call)
        ]
        assert len(attack_calls) == 0

    def test_turn_retaliates_on_ignore(self, test_args, test_pool):
        player = MagicMock()
        player.moves = 100
        player.roomid = 1
        player.save = MagicMock()

        wolf = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 1, "healthpoints": 35},
            pool=test_pool,
        )

        with patch("murdermotel.rabidwolf.io.echo"):
            with patch("murdermotel.rabidwolf.util.diceroll", return_value=1):
                with patch("murdermotel.rabidwolf.randomlib.randint", return_value=5):
                    result = librw.turn(
                        test_args, obj=wolf, player=player, ignored=True
                    )

        assert result is True
        assert player.moves < 100

    def test_turn_no_player_returns_false(self, test_args):
        result = librw.turn(test_args, obj=None, player=None)
        assert result is False

    def test_turn_no_obj_returns_false(self, test_args):
        player = MagicMock()
        player.roomid = 1
        result = librw.turn(test_args, obj=None, player=player)
        assert result is False


class TestWolfAutoAttackChance:
    def test_auto_attack_triggers_below_threshold(self, test_args, test_pool):
        player = MagicMock()
        player.moves = 100
        player.roomid = 1
        player.save = MagicMock()

        wolf = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 1, "healthpoints": 35},
            pool=test_pool,
        )

        with patch("murdermotel.rabidwolf.io.echo"):
            with patch("murdermotel.rabidwolf.util.diceroll", return_value=5):
                with patch("murdermotel.rabidwolf.randomlib.randint", return_value=5):
                    librw.wolf_attack_player(test_args, wolf, player=player)

        assert player.moves < 100

    def test_auto_attack_damage_11_to_20(self, test_args, test_pool):
        player = MagicMock()
        player.moves = 100
        player.roomid = 1
        player.save = MagicMock()

        wolf = librw.build(
            test_args,
            {"name": "rabidwolf", "roomid": 1, "healthpoints": 35},
            pool=test_pool,
        )

        with patch("murdermotel.rabidwolf.io.echo"):
            with patch("murdermotel.rabidwolf.randomlib.randint", return_value=1):
                librw.wolf_attack_player(test_args, wolf, player=player)

        assert player.moves == 89
