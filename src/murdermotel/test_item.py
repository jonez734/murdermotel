class TestItem:
    def test_init(self, test_args):
        from murdermotel import item as libitem

        result = libitem.init(test_args)
        assert result is True

    def test_access(self, test_args):
        from murdermotel import item as libitem

        assert libitem.access(test_args, "init") is True
        assert libitem.access(test_args, "run") is True
        assert libitem.access(test_args, "turn") is True
        assert libitem.access(test_args, "other") is False

    def test_buildargs(self, test_args):
        from murdermotel import item as libitem

        result = libitem.buildargs(test_args)
        assert result is None

    def test_main(self, test_args):
        from murdermotel import item as libitem

        result = libitem.main(test_args)
        assert result is True

    def test_item_short(self, test_args):
        from murdermotel import item as libitem

        i = libitem.Item(test_args)
        i.title = "Test Item"
        i.name = "test"
        assert i.short() == "Test Item"

        i.title = None
        assert i.short() == "Item: test"

    def test_item_str(self, test_args):
        from murdermotel import item as libitem

        i = libitem.Item(test_args)
        i.title = "Test Item"
        assert str(i) == "Test Item"

    def test_item_buildrec(self, test_args):
        from murdermotel import item as libitem

        i = libitem.Item(test_args)
        i.kind = "weapon"
        i.name = "knife"
        i.title = "Kitchen Knife"
        i.serial = 1
        i.modulepath = "item"
        i.state = "normal"
        rec = i.buildrec()
        assert rec["kind"] == "weapon"
        assert rec["name"] == "knife"
        assert rec["serial"] == 1
        assert rec["state"] == "normal"

    def test_item_save_no_pool(self, test_args):
        from murdermotel import item as libitem

        i = libitem.Item(test_args)
        result = i.save()
        assert result is False

    def test_load_no_pool(self, test_args):
        from murdermotel import item as libitem

        result = libitem.load(test_args, "knife", pool=None)
        assert result is None

    def test_getcount_no_pool(self, test_args):
        from murdermotel import item as libitem

        result = libitem.getcount(test_args, pool=None)
        assert result is None

    def test_getcount(self, test_args, test_pool):
        from murdermotel import item as libitem

        count = libitem.getcount(test_args, pool=test_pool)
        assert isinstance(count, int)
        assert count >= 0

    def test_build(self, test_args):
        from murdermotel import item as libitem

        rec = {
            "kind": "weapon",
            "modulepath": "item",
            "name": "knife",
            "serial": 1,
            "title": "Kitchen Knife",
            "state": "normal",
        }
        i = libitem.build(test_args, rec)
        assert i.name == "knife"
        assert i.title == "Kitchen Knife"
        assert i.kind == "weapon"
