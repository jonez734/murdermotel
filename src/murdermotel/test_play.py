class TestPlay:
    def test_init(self, test_args):
        from murdermotel import play as libplay

        result = libplay.init(test_args)
        assert result is True

    def test_access(self, test_args):
        from murdermotel import play as libplay

        result = libplay.access(test_args, "test")
        assert result is True

    def test_buildargs(self, test_args):
        from murdermotel import play as libplay

        result = libplay.buildargs(test_args)
        assert result is None

    def test_maintmode_no_player(self, test_args):
        from murdermotel import play as libplay

        result = libplay.maintmode(test_args)
        assert result is False

    def test_playgroundhelp_no_room(self, test_args):
        from murdermotel import play as libplay

        class FakePlayer:
            items = []

        result = libplay.playgroundhelp(player=FakePlayer())
        assert result is False

    def test_playgroundhelp_no_player(self, test_args):
        from murdermotel import play as libplay

        class FakeRoom:
            exits = {"north": None}

        result = libplay.playgroundhelp(room=FakeRoom())
        assert result is False
