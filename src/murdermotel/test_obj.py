import pytest


class TestObj:
    def test_registry_register(self):
        from murdermotel.obj import ObjectRegistry

        reg = ObjectRegistry()
        obj = type("FakeObj", (), {"roomid": 1})()
        reg.register(obj)
        assert obj in reg._objects

    def test_registry_unregister(self):
        from murdermotel.obj import ObjectRegistry

        reg = ObjectRegistry()
        obj = type("FakeObj", (), {"roomid": 1})()
        reg.register(obj)
        reg.unregister(obj)
        assert obj not in reg._objects

    def test_registry_get_by_room(self):
        from murdermotel.obj import ObjectRegistry

        reg = ObjectRegistry()
        obj1 = type("FakeObj", (), {"roomid": 1})()
        obj2 = type("FakeObj", (), {"roomid": 2})()
        obj3 = type("FakeObj", (), {"roomid": 1})()
        reg.register(obj1)
        reg.register(obj2)
        reg.register(obj3)
        results = reg.get_by_room(1)
        assert len(results) == 2
        assert obj1 in results
        assert obj3 in results

    def test_registry_get_by_name(self):
        from murdermotel.obj import ObjectRegistry

        reg = ObjectRegistry()
        obj = type("FakeObj", (), {"name": "testname"})()
        reg.register(obj)
        found = reg.get_by_name("testname")
        assert found is obj
        assert reg.get_by_name("nonexistent") is None

    def test_registry_all(self):
        from murdermotel.obj import ObjectRegistry

        reg = ObjectRegistry()
        obj1 = type("FakeObj", (), {"roomid": 1})()
        obj2 = type("FakeObj", (), {"roomid": 2})()
        reg.register(obj1)
        reg.register(obj2)
        all_objs = reg.all()
        assert len(all_objs) == 2
        assert obj1 in all_objs
        assert obj2 in all_objs

    def test_registry_clear(self):
        from murdermotel.obj import ObjectRegistry

        reg = ObjectRegistry()
        obj = type("FakeObj", (), {"roomid": 1})()
        reg.register(obj)
        reg.clear()
        assert len(reg._objects) == 0

    def test_obj_short(self, test_args):
        from murdermotel.obj import Obj

        o = Obj(test_args)
        o.classname = "TestClass"
        assert o.short() == "TestClass"

    def test_obj_load_no_pool(self, test_args):
        from murdermotel.obj import Obj

        o = Obj(test_args)
        o.fields = ()
        result = o.load("nonexistent", pool=None)
        assert result is False
