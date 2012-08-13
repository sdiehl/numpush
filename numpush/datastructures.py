from collections import MutableMapping

class UpdateDictMixin(object):
    """Makes dicts call `self.on_update` on modifications.
    """
    on_update = None

    def calls_update(name):
        def oncall(self, *args, **kw):
            rv = getattr(super(UpdateDictMixin, self), name)(*args, **kw)
            if self.on_update is not None:
                self.on_update(self)
            return rv
        oncall.__name__ = name
        return oncall

    __setitem__ = calls_update('__setitem__')
    __delitem__ = calls_update('__delitem__')
    clear = calls_update('clear')
    pop = calls_update('pop')
    popitem = calls_update('popitem')
    setdefault = calls_update('setdefault')
    update = calls_update('update')
    del calls_update

class CallbackDict(UpdateDictMixin, dict):

    def __init__(self, initial=None, on_update=None):
        dict.__init__(self, initial or ())
        self.on_update = on_update

    def __repr__(self):
        return '<%s %s>' % (
            self.__class__.__name__,
            dict.__repr__(self)
        )

class TypeConversionDict(dict):
    def get(self, key, default=None, type=None):
        try:
            rv = self[key]
            if type is not None:
                rv = type(rv)
        except (KeyError, ValueError):
            rv = default
        return rv

class ReverseLookupDict(MutableMapping):
    def __init__(self, inits):
        self._map = {}
        self.update(inits)

    def __getitem__(self, key):
        return self._map.__getitem__(key)

    def __setitem__(self, key, val):
        self._map.__setitem__(key, val)
        self._map.__setitem__(val, key)

    def __delitem__(self, key):
        self._map.__delitem__(self[key])
        self._map.__delitem__(key)

    def __iter__(self):
        return self._map.__iter__()

    def __len__(self):
        return self._map

class NumpyProxy(object):
    pass
