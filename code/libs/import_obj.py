#coding:utf-8

__import_obj_local__ = {}

class import_obj(object):

    def __init__(self, key):
        __import_obj_local__[key] = self
        self.__dict__["_real"] = None

    def __getattr__(self, attr):
        return getattr(self._real, attr)

    def __setattr__(self, attr, value):
        setattr(self._real, attr, value)

    def __delattr__(self, name):
        delattr(self._real, name)

    def __getitem__(self, key):
        return self._real[key]

    def __setitem__(self, key, value):
        self._real[key] = value

    def __delitem__(self, key):
        del self._real[key]

    def __repr__(self):
        return repr(self._real)

    def __str__(self):
        return str(self._real)

    def __iter__(self):
        return iter(self._real)

    def __len__(self):
        return len(self._real)

    def __contains__(self, key):
        return key in self._real

    def __nonzero__(self):
        return bool(self._real)

def import_obj_set(key, value):
    __import_obj_local__[key].__dict__["_real"] = value

if __name__ == "__main__":
    c = import_obj("c")
    import_obj_set("c", "good day")
    print c
