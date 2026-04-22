class TestRoom:
    def test_init(self, test_args):
        from murdermotel import room as libroom

        result = libroom.init(test_args)
        assert result is True

    def test_access(self, test_args):
        from murdermotel import room as libroom

        assert libroom.access(test_args, "init") is True
        assert libroom.access(test_args, "run") is True
        assert libroom.access(test_args, "turn") is True
        assert libroom.access(test_args, "other") is False

    def test_buildargs(self, test_args):
        from murdermotel import room as libroom

        result = libroom.buildargs(test_args)
        assert result is None

    def test_main(self, test_args):
        from murdermotel import room as libroom

        result = libroom.main(test_args)
        assert result is True

    def test_room_short(self, test_args):
        from murdermotel import room as libroom

        r = libroom.Room(test_args)
        r.title = "Test Room"
        r.id = 42
        assert r.short() == "Test Room"

    def test_room_short_no_title(self, test_args):
        from murdermotel import room as libroom

        r = libroom.Room(test_args)
        r.title = None
        r.id = 42
        assert r.short() == "Room 42"

    def test_room_buildrec(self, test_args):
        from murdermotel import room as libroom

        r = libroom.Room(test_args)
        r.id = 1
        r.title = "Test"
        r.shortname = "test"
        r.description = "A test room"
        r.modulepath = None
        r.exits = {"north": 2, "south": 3, "east": 4, "west": 5, "up": 0, "down": 0}
        r.north = 2
        r.south = 3
        r.east = 4
        r.west = 5
        r.up = 0
        r.down = 0
        rec = r.buildrec()
        assert rec["id"] == 1
        assert rec["title"] == "Test"
        assert rec["shortname"] == "test"
        assert rec["north"] == 2

    def test_room_finditem(self, test_args):
        from murdermotel import room as libroom

        r = libroom.Room(test_args)

        class FakeItem:
            def __init__(self, nm, ttl):
                self.name = nm
                self.title = ttl

        item = FakeItem("Knife", "Kitchen Knife")
        r.items = [item]
        assert r.finditem("knife") == 0
        assert r.finditem("Kitchen Knife") == 0
        assert r.finditem("nonexistent") is None

    def test_room_load_no_pool(self, test_args):
        from murdermotel import room as libroom

        result = libroom.load(test_args, "lobby", pool=None)
        assert result is False

    def test_room_getitems_no_pool(self, test_args):
        from murdermotel import room as libroom

        result = libroom.getitems(test_args, 1, pool=None)
        assert result == []

    def test_getcount_no_pool(self, test_args):
        from murdermotel import room as libroom

        result = libroom.getcount(test_args, pool=None)
        assert result is False

    def test_getcount(self, test_args, test_pool):
        from murdermotel import room as libroom

        count = libroom.getcount(test_args, pool=test_pool)
        assert isinstance(count, int)
        assert count >= 0

    def test_build(self, test_args):
        from murdermotel import room as libroom

        rec = {
            "id": 1,
            "title": "Lobby",
            "shortname": "lobby",
            "description": "Main lobby",
            "modulepath": None,
            "north": 2,
            "south": 3,
            "east": 4,
            "west": 5,
            "up": 0,
            "down": 0,
        }
        r = libroom.build(test_args, rec)
        assert r.title == "Lobby"
        assert r.shortname == "lobby"
