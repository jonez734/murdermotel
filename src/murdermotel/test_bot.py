import pytest


class TestBotQueries:
    def test_get_player_count(self, test_args, test_pool):
        from murdermotel import bot

        count = bot.get_player_count(test_args, pool=test_pool)
        assert isinstance(count, int)
        assert count >= 0

    def test_get_alive_bots(self, test_args, test_pool):
        from murdermotel import bot

        bots = bot.get_alive_bots(test_args, pool=test_pool)
        assert isinstance(bots, list)