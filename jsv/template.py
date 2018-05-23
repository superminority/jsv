from .decoder import scanstring, JSONDecodeError, WHITESPACE, WHITESPACE_STR, _CONSTANTS
from .scanner import py_make_scanner as make_scanner

class JSVObjectValues:
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


class JSVArrayValues:
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
    if isinstance(val, JSVObjectValues) or isinstance(val, JSVArrayValues) or isinstance(val, int) or isinstance(val, float) or\
            isinstance(val, str) or isinstance(val, bool) or val is None:
        return

    return TypeError('RecordDict argument must be another RecordDict, a RecordList, or a json primitive type')


class JSVObjectKeys:
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


class JSVArrayDef:
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
        return out


def check_key_element_type(obj):
    if isinstance(obj, str):
        return
    if isinstance(obj, tuple) and len(obj) == 2 and isinstance(obj[0], str) and\
            (isinstance(obj[1], JSVObjectKeys) or isinstance(obj[1], JSVArrayDef)):
        return

    return TypeError('KeyList elements must be of type `str` or tuples of the form `(str, KeyList or ArrayDef)`')


def check_arraydef_arg_type(obj):
    if obj is None or isinstance(obj, JSVObjectKeys) or isinstance(obj, JSVArrayDef):
        return

    return TypeError('ArrayDef argument must be of type `KeyList`, `ArrayDef`, or None')


def JSVTemplateObject(s_and_end, strict, scan_once, object_hook, object_pairs_hook,
                      memo=None, _w=WHITESPACE.match, _ws=WHITESPACE_STR):
    s, end = s_and_end
    keys = JSVObjectKeys()
    # Backwards compatibility
    if memo is None:
        memo = {}
    memo_get = memo.setdefault
    # Use a slice to prevent IndexError from being raised, the following
    # check will raise a more specific ValueError if the string is empty
    nextchar = s[end:end + 1]
    if nextchar != '"':
        if nextchar in _ws:
            end = _w(s, end).end()
            nextchar = s[end:end + 1]
        # Trivial empty object
        if nextchar == '}':
            if object_pairs_hook is not None:
                result = object_pairs_hook(keys)
                return result, end + 1
            keys = {}
            if object_hook is not None:
                keys = object_hook(keys)
            return keys, end + 1
        elif nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end)
    end += 1
    while True:
        key, end = scanstring(s, end, strict)
        if key in keys:
            raise KeyError('Cannot have duplicate key in dictionary')
        try:
            nextchar = s[end]
            if nextchar in _ws:
                end = _w(s, end + 1).end()
                nextchar = s[end]
        except IndexError:
            nextchar = ''
        end += 1

        if nextchar == '}':
            keys.append(key)
            break
        elif nextchar == ':':
            try:
                if s[end] in _ws:
                    end += 1
                    if s[end] in _ws:
                        end = _w(s, end + 1).end()
            except IndexError:
                pass
            try:
                template, end = scan_once(s, end)
            except StopIteration as err:
                raise JSONDecodeError("Expecting template", s, err.value) from None
            keys.append((key, template))
            end += 1
        elif nextchar == ',':
            keys.append(key)
        elif nextchar != ',':
            raise JSONDecodeError("Expecting ',' delimiter", s, end - 1)
        end = _w(s, end).end()
        try:
            nextchar = s[end:end + 1]
        except IndexError:
            nextchar = ''
        end += 1
        if nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end - 1)
    if object_pairs_hook is not None:
        result = object_pairs_hook(keys)
        return result, end
    if object_hook is not None:
        keys = object_hook(keys)
    return keys, end


class JSVArray:
    pass


class JSVDecoder(object):
    """Simple JSON <http://json.org> decoder
    Performs the following translations in decoding by default:
    +---------------+-------------------+
    | JSON          | Python            |
    +===============+===================+
    | object        | dict              |
    +---------------+-------------------+
    | array         | list              |
    +---------------+-------------------+
    | string        | str               |
    +---------------+-------------------+
    | number (int)  | int               |
    +---------------+-------------------+
    | number (real) | float             |
    +---------------+-------------------+
    | true          | True              |
    +---------------+-------------------+
    | false         | False             |
    +---------------+-------------------+
    | null          | None              |
    +---------------+-------------------+
    It also understands ``NaN``, ``Infinity``, and ``-Infinity`` as
    their corresponding ``float`` values, which is outside the JSON spec.
    """

    def __init__(self, *, object_hook=None, parse_float=None,
            parse_int=None, parse_constant=None, strict=True,
            object_pairs_hook=None):
        """``object_hook``, if specified, will be called with the result
        of every JSON object decoded and its return value will be used in
        place of the given ``dict``.  This can be used to provide custom
        deserializations (e.g. to support JSON-RPC class hinting).
        ``object_pairs_hook``, if specified will be called with the result of
        every JSON object decoded with an ordered list of pairs.  The return
        value of ``object_pairs_hook`` will be used instead of the ``dict``.
        This feature can be used to implement custom decoders that rely on the
        order that the key and value pairs are decoded (for example,
        collections.OrderedDict will remember the order of insertion). If
        ``object_hook`` is also defined, the ``object_pairs_hook`` takes
        priority.
        ``parse_float``, if specified, will be called with the string
        of every JSON float to be decoded. By default this is equivalent to
        float(num_str). This can be used to use another datatype or parser
        for JSON floats (e.g. decimal.Decimal).
        ``parse_int``, if specified, will be called with the string
        of every JSON int to be decoded. By default this is equivalent to
        int(num_str). This can be used to use another datatype or parser
        for JSON integers (e.g. float).
        ``parse_constant``, if specified, will be called with one of the
        following strings: -Infinity, Infinity, NaN.
        This can be used to raise an exception if invalid JSON numbers
        are encountered.
        If ``strict`` is false (true is the default), then control
        characters will be allowed inside strings.  Control characters in
        this context are those with character codes in the 0-31 range,
        including ``'\\t'`` (tab), ``'\\n'``, ``'\\r'`` and ``'\\0'``.
        """
        self.object_hook = object_hook
        self.parse_float = parse_float or float
        self.parse_int = parse_int or int
        self.parse_constant = parse_constant or _CONSTANTS.__getitem__
        self.strict = strict
        self.object_pairs_hook = object_pairs_hook
        self.parse_object = JSVTemplateObject
        self.parse_array = JSVArray
        self.parse_string = scanstring
        self.memo = {}
        self.scan_once = make_scanner(self)

    def decode(self, s, _w=WHITESPACE.match):
        """Return the Python representation of ``s`` (a ``str`` instance
        containing a JSON document).
        """
        obj, end = self.raw_decode(s, idx=_w(s, 0).end())
        end = _w(s, end).end()
        if end != len(s):
            raise JSONDecodeError("Extra data", s, end)
        return obj

    def raw_decode(self, s, idx=0):
        """Decode a JSON document from ``s`` (a ``str`` beginning with
        a JSON document) and return a 2-tuple of the Python
        representation and the index in ``s`` where the document ended.
        This can be used to decode a JSON document from a string that may
        have extraneous data at the end.
        """
        try:
            obj, end = self.scan_once(s, idx)
        except StopIteration as err:
            raise JSONDecodeError("Expecting value", s, err.value) from None
        return obj, end