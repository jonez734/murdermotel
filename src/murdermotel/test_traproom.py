class TestTrapRoom:
    def test_init(self, test_args):
        from murdermotel import traproom as libtraproom

        result = libtraproom.init(test_args)
        assert result is True

    def test_access(self, test_args):
        from murdermotel import traproom as libtraproom

        assert libtraproom.access(test_args, "init") is True
        assert libtraproom.access(test_args, "run") is True
        assert libtraproom.access(test_args, "turn") is True
        assert libtraproom.access(test_args, "attempt") is True
        assert libtraproom.access(test_args, "success") is True
        assert libtraproom.access(test_args, "other") is False

    def test_buildargs(self, test_args):
        from murdermotel import traproom as libtraproom

        result = libtraproom.buildargs(test_args)
        assert result is None

    def test_main(self, test_args):
        from murdermotel import traproom as libtraproom

        result = libtraproom.main(test_args)
        assert result is True

    def test_traproom_defaults(self, test_args):
        from murdermotel import traproom as libtraproom

        r = libtraproom.TrapRoom(test_args)
        assert r.attempts_allowed == 5
        assert r.trap_message == "You are trapped! Try again..."
        assert r.trap_exits is None
        assert r.escape_min == 10
        assert r.escape_max is None

    def test_traproom_custom_config(self, test_args):
        from murdermotel import traproom as libtraproom

        r = libtraproom.TrapRoom(test_args)
        r.attempts_allowed = 3
        r.trap_message = "Custom trap!"
        r.trap_exits = ("N", "S")
        r.escape_min = 20
        r.escape_max = 50

        assert r.attempts_allowed == 3
        assert r.trap_message == "Custom trap!"
        assert r.trap_exits == ("N", "S")
        assert r.escape_min == 20
        assert r.escape_max == 50

    def test_traproom_inherits_room(self, test_args):
        from murdermotel import traproom as libtraproom
        from murdermotel import room as libroom

        r = libtraproom.TrapRoom(test_args)
        assert isinstance(r, libroom.Room)
        assert r.id is None
        assert r.title is None
        assert r.exits == {}

    def test_attempt_first_try(self, test_args):
        from murdermotel import traproom as libtraproom

        class MockPlayer:
            moniker = "test_player"

        libtraproom._counter.clear()
        args = test_args
        kwargs = {"player": MockPlayer()}

        result = libtraproom.attempt(args, **kwargs)
        assert result is False
        assert libtraproom._counter["test_player"] == 1

    def test_attempt_after_5_tries(self, test_args):
        from murdermotel import traproom as libtraproom

        class MockPlayer:
            moniker = "test_player_5"

        libtraproom._counter.clear()
        args = test_args
        player = MockPlayer()

        for i in range(4):
            result = libtraproom.attempt(args, player=player)
            assert result is False, f"Attempt {i + 1} should be False"

        assert libtraproom._counter["test_player_5"] == 4

        result = libtraproom.attempt(args, player=player)
        assert result is True, "5th attempt should allow escape"
        assert libtraproom._counter["test_player_5"] == 5

    def test_attempt_no_player(self, test_args):
        from murdermotel import traproom as libtraproom

        result = libtraproom.attempt(test_args)
        assert result is True

    def test_reset_counter(self, test_args):
        from murdermotel import traproom as libtraproom

        class MockPlayer:
            moniker = "test_reset"

        libtraproom._counter.clear()
        args = test_args
        player = MockPlayer()

        libtraproom.attempt(args, player=player)
        libtraproom.attempt(args, player=player)
        assert libtraproom._counter["test_reset"] == 2

        libtraproom.reset(args, "test_reset")
        assert "test_reset" not in libtraproom._counter

    def test_turn_calls_attempt(self, test_args):
        from murdermotel import traproom as libtraproom

        class MockPlayer:
            moniker = "test_turn"

        libtraproom._counter.clear()
        args = test_args
        player = MockPlayer()

        result = libtraproom.turn(args, player=player)
        assert result is False
        assert libtraproom._counter["test_turn"] == 1


class TestInsideGlowingSphere:
    def test_init(self, test_args):
        from murdermotel import inside_glowing_sphere as libtrap

        result = libtrap.init(test_args)
        assert result is True

    def test_access(self, test_args):
        from murdermotel import inside_glowing_sphere as libtrap

        assert libtrap.access(test_args, "init") is True
        assert libtrap.access(test_args, "run") is True
        assert libtrap.access(test_args, "turn") is True
        assert libtrap.access(test_args, "attempt") is True
        assert libtrap.access(test_args, "success") is True

    def test_buildargs(self, test_args):
        from murdermotel import inside_glowing_sphere as libtrap

        result = libtrap.buildargs(test_args)
        assert result is None

    def test_main(self, test_args):
        from murdermotel import inside_glowing_sphere as libtrap

        result = libtrap.main(test_args)
        assert result is True

    def test_trap_exits_none(self, test_args):
        from murdermotel import inside_glowing_sphere as libtrap

        assert libtrap.TRAP_EXITS is None

    def test_custom_trap_class(self, test_args):
        from murdermotel import inside_glowing_sphere as libtraproom
        from murdermotel import traproom as libtrap

        r = libtraproom.GlowingSphereTrap(test_args)
        assert r.attempts_allowed == 5
        assert r.trap_message == "You are trapped in the glowing sphere! Try again..."
        assert isinstance(r, libtrap.TrapRoom)
