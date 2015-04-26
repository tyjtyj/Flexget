from __future__ import unicode_literals, division, absolute_import

import logging
from collections import MutableMapping
from copy import deepcopy

log = logging.getLogger('lazy_dict')


class LazyDict(MutableMapping):
    """
    A dictionary-like object, which supports fields that can be lazily evaluated.
    """

    def __init__(self, *args, **kwargs):
        self.store = {}
        # Store a mapping of keys to a list of callback functions that can provide them
        self.lazy_keys = {}
        self.update(*args, **kwargs)

    def __setitem__(self, key, value):
        self.store[key] = value
        self.lazy_keys.pop(key, None)

    def __len__(self):
        return len(self.store.keys() + self.lazy_keys.keys())

    def __iter__(self):
        return self.store.keys() + self.lazy_keys.keys()

    def __delitem__(self, key):
        if key not in self.store and key not in self.lazy_keys:
            raise KeyError(key)
        self.store.pop(key, None)
        self.lazy_keys.pop(key, None)

    def __getitem__(self, key):
        try:
            return self.store[key]
        except KeyError:
            return self.eval_lazy(key)

    def __copy__(self):
        return LazyDict(self)

    def register_lazy_keys(self, keys, func):
        """Register a list of keys to be lazily loaded by callback func.

        :param list keys: List of field names that are registered as lazy keys
        :param func:
          Callback function which is called when lazy field needs to be evaluated.
          Function should return a dict with new values.
        """
        for key in keys:
            if key not in self.store:
                self.lazy_keys.setdefault(key, []).append(func)

    def get(self, key, default=None, eval_lazy=True):
        """
        Like the normal :func:`dict.get` method, except lazy evaluation can be avoided.

        :param bool eval_lazy: If True, the default will be returned instead of calling lazy lookup functions.
        """
        try:
            return self.store[key]
        except KeyError:
            try:
                return self.eval_lazy(key, default)
            except KeyError:
                return default

    def update(self, *args, **kwargs):
        if args and isinstance(args[0], LazyDict):
            super(LazyDict, self).update(args[0].store)
            for key, funcs in args[0].lazy_keys.iteritems():
                if key in self.store:
                    continue
                for func in funcs:
                    if func not in self.lazy_keys.setdefault(key, []):
                        self.lazy_keys[key].append(func)
            args = []
        super(LazyDict, self).update(*args, **kwargs)

    def eval_lazy(self, key, default=None):
        """
        Runs callback functions to get value for given `key`.
        Also updates the store with all values provided by given callback function.
        """
        lazy_funcs = self.lazy_keys[key]
        for func in lazy_funcs[:]:
            result = None
            try:
                result = func()
            # except SomeException:  # TODO: declare an exception type these callbacks raise on clean failure
            except Exception:
                log.warning('Unknown error with callback func %r' % func, exc_info=True)
            if result:
                # Update the store, with already set values overriding new lazily evaluated ones
                for key in result:
                    if key not in self.store:
                        self[key] = result[key]
                if key not in self.store:
                    log.error('BUG: lazy callback function %r did not provide promised key `%s`' % (func, key))
                    continue
                return self.store[key]
        return default
