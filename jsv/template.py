class RecordDict:
    def __init__(self, *args):
        self._values = []
        for v in args:
            self.append(v)

    def append(self, val):
        e = check_value_type(val)
        if e:
            raise e
        self._values.append(val)

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if len(self._values) <= self._index:
            raise StopIteration
        out = self._values[self._index]
        self._index += 1
        return out


class RecordList:
    def __init__(self, *args):
        self._values = []
        for v in args:
            self.append(v)

    def append(self, val):
        e = check_value_type(val)
        if e:
            raise e
        self._values.append(val)

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if len(self._values) <= self._index:
            raise StopIteration
        out = self._values[self._index]
        self._index += 1
        return out


def check_value_type(val):
    if isinstance(val, RecordDict) or isinstance(val, RecordList) or isinstance(val, int) or isinstance(val, float) or\
            isinstance(val, str) or isinstance(val, bool) or val is None:
        return

    return TypeError('RecordDict argument must be another RecordDict, a RecordList, or a json primitive type')


class KeyList:
    def __init__(self, *args):
        self._values = []
        for k in args:
            self.append(k)

    def append(self, obj):
        e = check_key_element_type(obj)
        if e:
            raise e
        self._values.append(obj)

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if len(self._values) <= self._index:
            raise StopIteration
        out = self._values[self._index]
        self._index += 1
        return out

    def expand(self, rd):
        out = {}
        for k, r in zip(self, rd):
            if isinstance(k, str):
                out[k] = r
            else:
                out[k[0]] = k[1].expand(r)
        return out


class ArrayDef:
    def __init__(self, obj):
        e = check_arraydef_arg_type(obj)
        if e:
            raise e
        self._def = obj

    def expand(self, rl):
        out = []
        if self._def is None:
            for r in rl:
                out.append(r)
        else:
            for r in rl:
                out.append(self._def.expand(r))


def check_key_element_type(obj):
    if isinstance(obj, str):
        return
    if isinstance(obj, tuple) and len(obj) == 2 and isinstance(obj[0], str) and\
            (isinstance(obj[1], KeyList) or isinstance(obj[1], ArrayDef)):
        return

    return TypeError('KeyList elements must be of type `str` or tuples of the form `(str, KeyList or ArrayDef)`')


def check_arraydef_arg_type(obj):
    if obj is None or isinstance(obj, KeyList) or isinstance(obj, ArrayDef):
        return

    return TypeError('ArrayDef argument must be of type `KeyList`, `ArrayDef`, or None')
