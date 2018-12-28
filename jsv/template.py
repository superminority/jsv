import json
from collections import OrderedDict
from enum import unique, Enum
from re import compile


class JSVDecodeError(ValueError):

    def __init__(self, msg, pos):
        errmsg = '{0}: column {1:d}'.format(msg, pos)
        super().__init__(errmsg)


class JSVTemplateDecodeError(JSVDecodeError):
    """An error occurred while decoding a str or object into a :class:`.JSVTemplate`."""

    def __init__(self, msg, pos):
        super().__init__(msg, pos)


class JSVRecordDecodeError(JSVDecodeError):
    """An error occurred while decoding a str representing a record into an object."""

    def __init__(self, msg, pos):
        super().__init__(msg, pos)


class JSVTemplate:
    """Class for decoding and encoding json records in jsv format.

    A Template object stores the key structure for a json-compatible python object. It can then serialize or deserialize
    any object that conforms to that key structure in a string which is similar in structure to json, but in which the
    keys are omitted.

    Args:
        key_source (str or json-compatible object): if a string, this must be a valid template string; if not, a
            :class:`.JSVTemplateDecodeError` will be raised. If a json-compatible object, the key structure will be
            extracted, with keys in alphabetical order.
    """

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if type(self) is type(other):
            return str(self) == str(other)
        else:
            return False

    def __repr__(self):
        if isinstance(self._key_tree, list):
            return encode_template_list(self._key_tree)
        elif isinstance(self._key_tree, OrderedDict):
            return encode_template_dict(self._key_tree)
        else:
            return '{}'

    def __init__(self, key_source='{}'):
        if isinstance(key_source, str):
            template_str = key_source
        elif isinstance(key_source, dict) or isinstance(key_source, list)\
                or isinstance(key_source, tuple) or key_source is None:
            template_str = get_template_str(key_source)
        else:
            raise TypeError('Expecting a string, dict, list or None')
        self._key_tree = parse_template_string(template_str)

    def encode(self, obj):
        """Encode a json-compatible object into jsv
        
        Args:
            obj (json-compatible object): obj must also conform to the key structure of the Template, otherwise
                an error will be raised.
        """
        c = self._key_tree

        if isinstance(c, OrderedDict):
            return encode_dict(obj, c)
        elif isinstance(c, list):
            return encode_list(obj, c)
        else:
            return json_encode(obj)

    def decode(self, s):
        """Decode a jsv string into a json-compatible object
        
        Args:
            s (str): s represents a json object that has been encoded with the given template. If it does not conform
                to the template, or is not parsable as jsv, a :class:`.JSVRecordDecodeError` will be raised.
        """
        c = self._key_tree
        if isinstance(s, str):
            char_list = list(reversed(s))
        elif isinstance(s, list):
            char_list = s
        else:
            raise TypeError('argument `s` must be a string or a list of characters')

        def ex_loc(cl):
            return len(s) - len(cl) - 1

        if c is None:
            return get_json_value(char_list, ex_loc)
        if isinstance(c, list):
            out = []
            it = iter(c)
            decode_array_entries(char_list, out, it, ex_loc)
            return out
        else:
            out = {}
            it = is_last(c.items())
            decode_dict_entries(char_list, out, it, ex_loc)
            return out


def encode_dict(obj, fm):
    if not isinstance(obj, dict):
        raise ValueError('Expecting a dictionary')

    entries = [''] * len(fm)
    indexes = list(fm.keys())
    for k, v in sorted(obj.items()):
        if k in fm:
            child_fm = fm[k]
            if isinstance(child_fm, OrderedDict):
                entries[indexes.index(k)] = encode_dict(v, child_fm)
            elif isinstance(child_fm, list):
                entries[indexes.index(k)] = encode_list(v, child_fm)
            else:
                entries[indexes.index(k)] = json_encode(v)
        else:
            entries.append('"{0}":{1}'.format(k, json_encode(v)))

    return '{{{}}}'.format(','.join(entries))


def encode_list(arr, fm):
    if not (isinstance(arr, list) or isinstance(arr, tuple)):
        raise ValueError('Expecting a list or tuple')

    entries = []
    for i, v in enumerate(arr):
        if i < len(fm):
            child_fm = fm[i]
        else:
            child_fm = fm[-1]
        if isinstance(child_fm, OrderedDict):
            entries.append(encode_dict(v, child_fm))
        elif isinstance(child_fm, list):
            entries.append(encode_list(v, child_fm))
        else:
            entries.append(json_encode(v))

    return '[{}]'.format(','.join(entries))


def decode_dict_entries(char_list, obj, it, ex_loc):

    consume_next(char_list, {'{'}, ex_loc)
    isl, (k, v) = next(it)

    ws_trim(char_list)
    if char_list[-1] not in ({'}', ','} if isl else {','}):
        if v is None:
            obj[k] = get_json_value(char_list, ex_loc)
        elif isinstance(v, list):
            n = []
            obj[k] = n
            it_next = iter(v)
            decode_array_entries(char_list, n, it_next, ex_loc)
        else:
            n = {}
            obj[k] = n
            it_next = is_last(v.items())
            decode_dict_entries(char_list, n, it_next, ex_loc)

    for isl, (k, v) in it:
        consume_next(char_list, {','}, ex_loc)
        ws_trim(char_list)
        if char_list[-1] not in ({'}', ','} if isl else {','}):
            if v is None:
                obj[k] = get_json_value(char_list, ex_loc)
            elif isinstance(v, list):
                n = []
                obj[k] = n
                it_next = iter(v)
                decode_array_entries(char_list, n, it_next, ex_loc)
            else:
                n = {}
                obj[k] = n
                it_next = is_last(v.items())
                decode_dict_entries(char_list, n, it_next, ex_loc)

    while True:
        if consume_next(char_list, {'}', ','}, ex_loc) == '}':
            break
        k, v = get_key_value_pair(char_list, ex_loc)
        obj[k] = v


def decode_array_entries(char_list, arr, it, ex_loc):

    consume_next(char_list, {'['}, ex_loc)
    c = next(it)

    ws_trim(char_list)
    if char_list[-1] == ']':
        char_list.pop()
        return

    if c is None:
        arr.append(get_json_value(char_list, ex_loc))
    elif isinstance(c, list):
        n = []
        arr.append(n)
        it_next = iter(c)
        decode_array_entries(char_list, n, it_next, ex_loc)
    else:
        n = {}
        arr.append(n)
        it_next = is_last(c.items())
        decode_dict_entries(char_list, n, it_next, ex_loc)

    for c in it:
        if consume_next(char_list, {',', ']'}, ex_loc) == ']':
            return
        if c is None:
            arr.append(get_json_value(char_list, ex_loc))
        elif isinstance(c, list):
            n = []
            arr.append(n)
            it_next = iter(c)
            decode_array_entries(char_list, n, it_next, ex_loc)
        else:
            n = {}
            arr.append(n)
            it_next = is_last(c.items())
            decode_dict_entries(char_list, n, it_next, ex_loc)

    while True:
        if consume_next(char_list, {']', ','}, ex_loc) == ']':
            break
        if c is None:
            arr.append(get_json_value(char_list, ex_loc))
        elif isinstance(c, list):
            n = []
            arr.append(n)
            it_next = iter(c)
            decode_array_entries(char_list, n, it_next, ex_loc)
        else:
            n = {}
            arr.append(n)
            it_next = is_last(c.items())
            decode_dict_entries(char_list, n, it_next, ex_loc)


string_escape_dict = {
    '"': '\\"',
    '\\': '\\\\',
    '\b': '\\b',
    '\f': '\\f',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t'
}


def encode_string(s):
    out_arr = []
    for c in s:
        if c in string_escape_dict:
            out_arr.append(string_escape_dict[c])
        elif ord(c) < 128:
            out_arr.append(c)
        else:
            out_arr.append('\\u' + hex(ord(c))[2:].zfill(4))
    return ''.join(out_arr)


def encode_template_dict(kt):
    out_arr = []
    for k, v in kt.items():
        if v:
            if isinstance(v, list):
                out_arr.append('"{0}":{1}'.format(encode_string(k), encode_template_list(v)))
            else:
                out_arr.append('"{0}":{1}'.format(encode_string(k), encode_template_dict(v)))
        else:
            out_arr.append('"{}"'.format(encode_string(k)))

    return '{{{}}}'.format(','.join(out_arr))


def encode_template_list(kt):
    out_arr = []
    for v in kt:
        if v:
            if isinstance(v, list):
                out_arr.append(encode_template_list(v))
            else:
                out_arr.append(encode_template_dict(v))
        else:
            out_arr.append('')

    return '[{}]'.format(','.join(out_arr))


@unique
class TemplateStates(Enum):
    DONE = 0
    EXPECT_ARRAY_OR_OBJECT_OR_ARRAY_CLOSE = 1
    EXPECT_ARRAY_OR_OBJECT = 2
    ARRAY_NEXT_OR_CLOSE = 3
    OBJECT_AFTER_KEY = 4
    OBJECT_NEXT_OR_CLOSE = 5
    EXPECT_QUOTE = 6


def parse_template_string(s):
    if len(s.strip()) <= 0:
        return None
    state = TemplateStates.EXPECT_ARRAY_OR_OBJECT
    char_list = list(reversed(s))
    val = None
    stack = []
    has_keys = []

    def ex_loc(cl):
        return len(s) - len(cl) - 1

    while state is not TemplateStates.DONE:
        try:
            current_char = char_list.pop()
        except IndexError:
            raise JSVTemplateDecodeError('End of string reached unexpectedly', ex_loc(char_list))

        # --------------------------------------------
        # State: EXPECT_ARRAY_OR_OBJECT_OR_ARRAY_CLOSE
        # --------------------------------------------
        if state is TemplateStates.EXPECT_ARRAY_OR_OBJECT_OR_ARRAY_CLOSE:
            if current_char.isspace():
                pass
            elif current_char == '{':
                stack.append(OrderedDict())
                has_keys.append(False)
                state = TemplateStates.EXPECT_QUOTE
            elif current_char == '[':
                stack.append([])
                has_keys.append(False)
            elif current_char == ',':
                stack[-1].append(None)
            elif current_char == ']':
                stack[-1].append(None)
                if has_keys.pop():
                    val = stack.pop()
                    prune_array_end(val)
                else:
                    stack.pop()
                    val = None
                if stack:
                    if isinstance(stack[-1], list):
                        stack[-1].append(val)
                        state = TemplateStates.ARRAY_NEXT_OR_CLOSE
                    else:
                        key = stack.pop()
                        stack[-1].update({key: val})
                        state = TemplateStates.OBJECT_NEXT_OR_CLOSE
                else:
                    state = TemplateStates.DONE
            else:
                raise JSVTemplateDecodeError(
                    'Expecting `{{`, `[` or `]`, got `{}`'.format(current_char), ex_loc(char_list))

        # -----------------------------
        # State: EXPECT_ARRAY_OR_OBJECT
        # -----------------------------
        elif state is TemplateStates.EXPECT_ARRAY_OR_OBJECT:
            if current_char.isspace():
                pass
            elif current_char == '{':
                stack.append(OrderedDict())
                has_keys.append(False)
                state = TemplateStates.EXPECT_QUOTE
            elif current_char == '[':
                stack.append([])
                has_keys.append(False)
                state = TemplateStates.EXPECT_ARRAY_OR_OBJECT_OR_ARRAY_CLOSE
            else:
                raise JSVTemplateDecodeError('Expecting `{{` or `[`, got `{}`'.format(current_char), ex_loc(char_list))

        # --------------------------
        # State: ARRAY_NEXT_OR_CLOSE
        # --------------------------
        elif state is TemplateStates.ARRAY_NEXT_OR_CLOSE:
            if current_char.isspace():
                pass
            elif current_char == ',':
                state = TemplateStates.EXPECT_ARRAY_OR_OBJECT_OR_ARRAY_CLOSE
            elif current_char == ']':
                if has_keys.pop():
                    val = stack.pop()
                    prune_array_end(val)
                else:
                    stack.pop()
                    val = None
                if stack:
                    if isinstance(stack[-1], list):
                        stack[-1].append(val)
                        state = TemplateStates.ARRAY_NEXT_OR_CLOSE
                    else:
                        key = stack.pop()
                        stack[-1].update({key: val})
                        state = TemplateStates.OBJECT_NEXT_OR_CLOSE
                else:
                    state = TemplateStates.DONE
            else:
                raise JSVTemplateDecodeError('Expecting `,` or `]`, got `{}`'.format(current_char), ex_loc(char_list))

        # -----------------------
        # State: OBJECT_AFTER_KEY
        # -----------------------
        elif state is TemplateStates.OBJECT_AFTER_KEY:
            if current_char.isspace():
                pass
            elif current_char == ',':
                key = stack.pop()
                stack[-1].update({key: None})
                state = TemplateStates.EXPECT_QUOTE
            elif current_char == ':':
                state = TemplateStates.EXPECT_ARRAY_OR_OBJECT
            elif current_char == '}':
                key = stack.pop()
                val = stack.pop()
                has_keys.pop()
                val.update({key: None})
                if stack:
                    if isinstance(stack[-1], list):
                        stack[-1].append(val)
                        state = TemplateStates.ARRAY_NEXT_OR_CLOSE
                    else:
                        key = stack.pop()
                        stack[-1].update({key: val})
                        state = TemplateStates.OBJECT_NEXT_OR_CLOSE
                else:
                    state = TemplateStates.DONE
            else:
                raise JSVTemplateDecodeError(
                    'Expecting `,`, `:`, or `}}`, got `{}`'.format(current_char), ex_loc(char_list))

        # ---------------------------
        # State: OBJECT_NEXT_OR_CLOSE
        # ---------------------------
        elif state is TemplateStates.OBJECT_NEXT_OR_CLOSE:
            if current_char.isspace():
                pass
            elif current_char == ',':
                state = TemplateStates.EXPECT_QUOTE
            elif current_char == '}':
                val = stack.pop()
                val = val if has_keys.pop() else None
                if stack:
                    if isinstance(stack[-1], list):
                        stack[-1].append(val)
                        state = TemplateStates.ARRAY_NEXT_OR_CLOSE
                    else:
                        key = stack.pop()
                        stack[-1].update({key: val})
                else:
                    state = TemplateStates.DONE
            else:
                raise JSVTemplateDecodeError('Expecting `,` or `}}`, got `{}`'.format(current_char), ex_loc(char_list))

        # -------------------
        # State: EXPECT_QUOTE
        # -------------------
        elif state is TemplateStates.EXPECT_QUOTE:
            if current_char.isspace():
                pass
            elif current_char == '"':
                stack.append(get_json_string(char_list, ex_loc, 'template'))
                state = TemplateStates.OBJECT_AFTER_KEY
                has_keys = [True] * len(has_keys)
            elif current_char == '}':
                val = None
                stack.pop()
                has_keys.pop()
                if stack:
                    if isinstance(stack[-1], list):
                        stack[-1].append(val)
                        state = TemplateStates.ARRAY_NEXT_OR_CLOSE
                    else:
                        key = stack.pop()
                        stack[-1].update({key: val})
                        state = TemplateStates.OBJECT_NEXT_OR_CLOSE
                else:
                    state = TemplateStates.DONE
            else:
                raise JSVTemplateDecodeError('Expecting `"`, got `{}`'.format(current_char), ex_loc(char_list))

    return val


def get_json_value(char_list, ex_loc):
    s = ''.join(reversed(char_list))
    start_len = len(s)
    s = s.lstrip()
    end_len = len(s)
    d = json.JSONDecoder()
    try:
        v, r = d.raw_decode(s)
    except ValueError:
        raise JSVRecordDecodeError('Error decoding raw json', ex_loc(char_list))
    for i in range(r + start_len - end_len):
        char_list.pop()
    return v


def get_key_value_pair(char_list, ex_loc):
    current_char = ''
    while current_char != '"':
        try:
            current_char = char_list.pop()
        except IndexError as ex:
            raise JSVRecordDecodeError(
                'End of string reached unexpectedly while awaiting `"`', ex_loc(char_list)) from ex

        if not current_char.isspace() and not current_char == '"':
            raise JSVRecordDecodeError('Expecting `"`', ex_loc(char_list))

    k = get_json_string(char_list, ex_loc)

    current_char = ''
    while current_char != ':':
        try:
            current_char = char_list.pop()
        except IndexError as ex:
            raise JSVRecordDecodeError(
                'End of string reached unexpectedly while awaiting `:`', ex_loc(char_list)) from ex

        if not current_char.isspace() and not current_char == ':':
            raise JSVRecordDecodeError('Expecting `:`', ex_loc(char_list))

    v = get_json_value(char_list, ex_loc)
    return k, v


@unique
class StringStates(Enum):
    STRING_NEXT_OR_CLOSE = 0
    STRING_ESCAPE = 1
    STRING_HEX = 2


def get_json_string(char_list, ex_loc, source='record'):
    state = StringStates.STRING_NEXT_OR_CLOSE
    string_array = []

    while True:
        try:
            current_char = char_list.pop()
        except IndexError as ex:
            if source == 'record':
                raise JSVRecordDecodeError('End of string reached unexpectedly', ex_loc(char_list)) from ex
            else:
                raise JSVTemplateDecodeError('End of string reached unexpectedly', ex_loc(char_list)) from ex

        # ---------------------------
        # State: STRING_NEXT_OR_CLOSE
        # ---------------------------
        if state is StringStates.STRING_NEXT_OR_CLOSE:
            if current_char == '"':
                return ''.join(string_array)
            elif current_char == '\\':
                state = StringStates.STRING_ESCAPE
            else:
                string_array.append(current_char)

        # --------------------
        # State: STRING_ESCAPE
        # --------------------
        elif state is StringStates.STRING_ESCAPE:
            if current_char == '"':
                string_array.append('"')
                state = StringStates.STRING_NEXT_OR_CLOSE
            elif current_char == '\\':
                string_array.append('\\')
                state = StringStates.STRING_NEXT_OR_CLOSE
            elif current_char == 'b':
                string_array.append('\b')
                state = StringStates.STRING_NEXT_OR_CLOSE
            elif current_char == 'f':
                string_array.append('\f')
                state = StringStates.STRING_NEXT_OR_CLOSE
            elif current_char == 'n':
                string_array.append('\n')
                state = StringStates.STRING_NEXT_OR_CLOSE
            elif current_char == 'r':
                string_array.append('\r')
                state = StringStates.STRING_NEXT_OR_CLOSE
            elif current_char == 't':
                string_array.append('\t')
                state = StringStates.STRING_NEXT_OR_CLOSE
            elif current_char == 'u':
                hex_array = []
                state = StringStates.STRING_HEX
            else:
                if source == 'record':
                    raise JSVRecordDecodeError('expecting valid escape character', ex_loc(char_list))
                else:
                    raise JSVTemplateDecodeError('expecting valid escape character', ex_loc(char_list))

        # -----------------
        # State: STRING_HEX
        # -----------------
        elif state is StringStates.STRING_HEX:
            if hex_re.search(current_char):
                hex_array.append(current_char)
                if len(hex_array) >= 4:
                    print(''.join(hex_array))
                    string_array.append(chr(int(''.join(hex_array), 16)))
                    state = StringStates.STRING_NEXT_OR_CLOSE
            else:
                if source == 'record':
                    raise JSVRecordDecodeError('Expected a hex character ([0-9A-Fa-f])', ex_loc(char_list))
                else:
                    raise JSVTemplateDecodeError('Expected a hex character ([0-9A-Fa-f])', ex_loc(char_list))


def get_template_str(obj):
    if not obj:
        return ''

    if isinstance(obj, dict):
        return obj_to_template_str(obj)
    elif isinstance(obj, list) or isinstance(obj, tuple):
        return arr_to_template_str(obj)


def obj_to_template_str(obj):
    if len(obj) <= 0:
        return None

    out_arr = []
    for k, v in sorted(obj.items()):
        if isinstance(v, dict):
            obj_str = obj_to_template_str(v)
        elif isinstance(v, list) or isinstance(v, tuple):
            obj_str = arr_to_template_str(v)
        else:
            obj_str = None

        if obj_str is None:
            out_arr.append('"{}"'.format(k))
        else:
            out_arr.append('"{0}":{1}'.format(k, obj_str))

    return '{{{}}}'.format(','.join(out_arr))


def arr_to_template_str(arr):
    if len(arr) == 0:
        return None

    out_arr = []
    for v in arr:
        if isinstance(v, dict):
            arr_str = obj_to_template_str(v)
        elif isinstance(v, list) or isinstance(v, tuple):
            arr_str = arr_to_template_str(v)
        else:
            arr_str = None

        if arr_str is None:
            out_arr.append('')
        else:
            out_arr.append('{}'.format(arr_str))

    return '[{}]'.format(','.join(out_arr))


def consume_next(char_list, char_set, ex_loc):
    while True:
        try:
            c = char_list.pop()
        except IndexError as ex:
            raise JSVRecordDecodeError('End of string reached unexpectedly', ex_loc(char_list)) from ex

        if c in char_set:
            return c
        elif not c.isspace():
            raise JSVRecordDecodeError('Unexpected character `{}` encountered'.format(c), ex_loc(char_list))


def ws_trim(char_list):
    if char_list[-1].isspace():
        char_list.pop()


def prune_array_end(arr):
    if len(arr) < 2:
        return

    while True:
        if arr[-1] == arr[-2]:
            arr.pop()
            if len(arr) < 2:
                break
        else:
            break


def is_last(v):
    it = iter(v)
    e = next(it)
    while True:
        try:
            nxt = next(it)
            yield (False, e)
            e = nxt
        except StopIteration:
            yield (True, e)
            break


hex_re = compile('[0-9a-fA-F]')
json_encode = json.JSONEncoder(separators=(',', ':')).encode
