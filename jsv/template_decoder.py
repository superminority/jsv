from enum import Enum, auto, unique
from re import compile
import json

from .template import JSVArrayTemplate, JSVObjectTemplate


@unique
class TemplateStates(Enum):
    DONE = auto()
    EXPECT_ARRAY_OR_OBJECT_OR_ARRAY_CLOSE = auto()
    EXPECT_ARRAY_OR_OBJECT = auto()
    ARRAY_NEXT_OR_CLOSE = auto()
    OBJECT_AFTER_KEY = auto()
    OBJECT_NEXT_OR_CLOSE = auto()
    STRING_NEXT_OR_CLOSE = auto()
    STRING_ESCAPE = auto()
    STRING_HEX = auto()
    EXPECT_QUOTE_OR_CLOSE = auto()
    EXPECT_QUOTE = auto()


@unique
class RecordStates(Enum):
    DONE = auto()
    EXPECT_LITERAL = auto()
    EXPECT_OBJECT_START = auto()
    EXPECT_OBJECT_END = auto()
    EXPECT_ARRAY_START = auto()
    EXPECT_ARRAY_END = auto()


hex_re = compile('[0-9a-fA-F]')


def json_remainder(s):
    d = json.JSONDecoder()
    v, r = d.raw_decode(s)
    return v, s[r:].lstrip()


class Template:
    def parse_record(self, s):
        char_list = list(reversed(s))

    @property
    def remainder(self):
        return self._remainder

    def __eq__(self, other):
        return self._root == other

    def __init__(self, s):

        if isinstance(s, str):
            state = TemplateStates.EXPECT_ARRAY_OR_OBJECT
            char_list = list(reversed(s))
            stack = []
            current_obj = None

            while state is not TemplateStates.DONE:
                try:
                    current_char = char_list.pop()
                except IndexError:
                    raise IndexError('End of string reached unexpectedly')

                # --------------------------------------------
                # State: EXPECT_ARRAY_OR_OBJECT_OR_ARRAY_CLOSE
                # --------------------------------------------
                if state is TemplateStates.EXPECT_ARRAY_OR_OBJECT_OR_ARRAY_CLOSE:
                    if current_char.isspace():
                        pass
                    elif current_char == '{':
                        n = JSVObjectTemplate()
                        current_obj = n
                        stack.append(current_obj)
                        state = TemplateStates.EXPECT_QUOTE_OR_CLOSE
                    elif current_char == '[':
                        current_obj = JSVArrayTemplate()
                        stack.append(current_obj)
                    elif current_char == ']':
                        v = stack.pop()
                        if stack:
                            current_obj = stack[-1]
                            if isinstance(current_obj, str):
                                k = stack.pop()
                                current_obj = stack[-1]
                                current_obj.append((k, v))
                                state = TemplateStates.OBJECT_NEXT_OR_CLOSE
                            elif isinstance(current_obj, JSVArrayTemplate):
                                current_obj.append(v)
                        else:
                            current_obj = v
                            state = TemplateStates.DONE
                    else:
                        raise ValueError('Expecting `{`, `[` or `]`')

                # -----------------------------
                # State: EXPECT_ARRAY_OR_OBJECT
                # -----------------------------
                elif state is TemplateStates.EXPECT_ARRAY_OR_OBJECT:
                    if current_char.isspace():
                        pass
                    elif current_char == '{':
                        n = JSVObjectTemplate()
                        if current_obj and isinstance(current_obj, JSVArrayTemplate):
                            current_obj.append(n)
                        current_obj = n
                        stack.append(current_obj)
                        state = TemplateStates.EXPECT_QUOTE_OR_CLOSE
                    elif current_char == '[':
                        current_obj = JSVArrayTemplate()
                        stack.append(current_obj)
                        state = TemplateStates.EXPECT_ARRAY_OR_OBJECT_OR_ARRAY_CLOSE
                    else:
                        raise ValueError('Expecting `{` or `[`')

                # --------------------------
                # State: ARRAY_NEXT_OR_CLOSE
                # --------------------------
                elif state is TemplateStates.ARRAY_NEXT_OR_CLOSE:
                    if current_char.isspace():
                        pass
                    elif current_char == ',':
                        state = TemplateStates.EXPECT_ARRAY_OR_OBJECT
                    elif current_char == ']':
                        v = stack.pop()
                        if stack:
                            current_obj = stack[-1]
                            if isinstance(current_obj, str):
                                k = stack.pop()
                                current_obj = stack[-1]
                                current_obj.append((k, v))
                                state = TemplateStates.OBJECT_NEXT_OR_CLOSE
                            elif isinstance(current_obj, JSVArrayTemplate):
                                current_obj.append(v)
                        else:
                            current_obj = v
                            state = TemplateStates.DONE
                    else:
                        raise ValueError('Expecting `,` or `]`')

                # -----------------------
                # State: OBJECT_AFTER_KEY
                # -----------------------
                elif state is TemplateStates.OBJECT_AFTER_KEY:
                    if current_char.isspace():
                        pass
                    elif current_char == ',':
                        k = stack.pop()
                        current_obj = stack[-1]
                        current_obj.append(k)
                        state = TemplateStates.EXPECT_QUOTE
                    elif current_char == ':':
                        state = TemplateStates.EXPECT_ARRAY_OR_OBJECT
                    elif current_char == '}':
                        k = stack.pop()
                        v = stack.pop()
                        v.append(k)
                        if stack:
                            current_obj = stack[-1]
                            if isinstance(current_obj, str):
                                k2 = stack.pop()
                                current_obj = stack[-1]
                                current_obj.append((k2, v))
                            else:
                                current_obj.append(v)
                            if isinstance(current_obj, JSVObjectTemplate):
                                state = TemplateStates.OBJECT_NEXT_OR_CLOSE
                            else:
                                state = TemplateStates.ARRAY_NEXT_OR_CLOSE
                        else:
                            current_obj = v
                            state = TemplateStates.DONE
                    else:
                        raise ValueError('Expecting `,`, `:`, or `}`')

                # ---------------------------
                # State: OBJECT_NEXT_OR_CLOSE
                # ---------------------------
                elif state is TemplateStates.OBJECT_NEXT_OR_CLOSE:
                    if current_char.isspace():
                        pass
                    elif current_char == ',':
                        v = current_obj
                        current_obj = stack[-1]
                        current_obj.append(v)
                        state = TemplateStates.EXPECT_ARRAY_OR_OBJECT
                    elif current_char == '}':
                        v = stack.pop()
                        if stack:
                            current_obj = stack[-1]
                            if isinstance(current_obj, str):
                                k = stack.pop()
                                current_obj = stack[-1]
                                current_obj.append((k, v))
                            elif isinstance(current_obj, JSVArrayTemplate):
                                current_obj.append(v)
                                state = TemplateStates.ARRAY_NEXT_OR_CLOSE
                        else:
                            state = TemplateStates.DONE
                    else:
                        raise ValueError('Expecting `,` or `}`')

                # ---------------------------
                # State: STRING_NEXT_OR_CLOSE
                # ---------------------------
                elif state is TemplateStates.STRING_NEXT_OR_CLOSE:
                    if current_char == '"':
                        v = stack.pop()
                        stack.append(''.join(v))
                        current_obj = stack[-1]
                        state = TemplateStates.OBJECT_AFTER_KEY
                    elif current_char == '\\':
                        state = TemplateStates.STRING_ESCAPE
                    else:
                        current_obj.append(current_char)

                # --------------------
                # State: STRING_ESCAPE
                # --------------------
                elif state is TemplateStates.STRING_ESCAPE:
                    if current_char == '"':
                        current_obj.append('"')
                    elif current_char == '\\':
                        current_obj.append('\\')
                    elif current_char == '/':
                        current_obj.append('/')
                    elif current_char == 'b':
                        current_obj.append('\b')
                    elif current_char == 'f':
                        current_obj.append('\f')
                    elif current_char == 'n':
                        current_obj.append('\n')
                    elif current_char == 'r':
                        current_obj.append('\r')
                    elif current_char == 't':
                        current_obj.append('\t')
                    elif current_char == 'u':
                        current_obj = []
                        stack.append(current_obj)
                        state = TemplateStates.STRING_HEX
                    else:
                        raise ValueError('expecting valid escape character')

                # -----------------
                # State: STRING_HEX
                # -----------------
                elif state is TemplateStates.STRING_HEX:
                    if hex_re.search(current_char):
                        current_obj.append(current_char)
                        if len(current_obj) >= 4:
                            v = stack.pop()
                            current_obj = stack[-1]
                            current_obj.append(bytearray.fromhex(''.join(v)).decode())
                            state = TemplateStates.STRING_NEXT_OR_CLOSE
                        else:
                            current_obj.append(current_char)
                    else:
                        raise ValueError('Expected a hex character ([0-9A-Fa-f]), got {}'.format(current_char))

                # ----------------------------
                # State: EXPECT_QUOTE_OR_CLOSE
                # ----------------------------
                elif state is TemplateStates.EXPECT_QUOTE_OR_CLOSE:
                    if current_char.isspace():
                        pass
                    elif current_char == '"':
                        current_obj = []
                        stack.append(current_obj)
                        state = TemplateStates.STRING_NEXT_OR_CLOSE
                    elif current_char == '}':
                        v = stack.pop()
                        if stack:
                            current_obj = stack[-1]
                            if isinstance(current_obj, str):
                                k = stack.pop()
                                current_obj = stack[-1]
                                current_obj.append((k, v))
                                state = TemplateStates.OBJECT_NEXT_OR_CLOSE
                            elif isinstance(current_obj, JSVArrayTemplate):
                                current_obj.append(v)
                                state = TemplateStates.ARRAY_NEXT_OR_CLOSE
                        else:
                            state = TemplateStates.DONE
                    else:
                        raise ValueError('Expecting `"` or `}`')

                # -------------------
                # State: EXPECT_QUOTE
                # -------------------
                elif state is TemplateStates.EXPECT_QUOTE:
                    if current_char.isspace():
                        pass
                    elif current_char == '"':
                        current_obj = []
                        stack.append(current_obj)
                        state = TemplateStates.STRING_NEXT_OR_CLOSE
                    else:
                        raise ValueError('Expecting `"`')
        elif isinstance(s, JSVArrayTemplate) or isinstance(JSVObjectTemplate):
            self._root = s
        else:
            raise TypeError('Expecting a string, a `JSVArrayTemplate` object, or a `JSVObjectTemplate` object')

        self._root = current_obj
        self._remainder = ''.join(reversed(char_list))
        rs = []

        if isinstance(self._root, JSVObjectTemplate):
            self.linearize_object(self._root, rs)
        elif isinstance(self._root, JSVArrayTemplate):
            self.linearize_array(self._root, rs)
        elif self._root is None:
            rs = [RecordStates.EXPECT_LITERAL]

        self._record_states = tuple(rs)

    @staticmethod
    def linearize_object(t, a):
        for v in t:
            if isinstance(v, str):
                a.append((RecordStates.EXPECT_LITERAL, v))
            elif isinstance(v[1], JSVObjectTemplate):
                a.append((RecordStates.EXPECT_OBJECT_START, v[0]))
                Template.linearize_object(v[1], a)
            elif isinstance(v[1], JSVArrayTemplate):
                a.append((RecordStates.EXPECT_ARRAY_START, v[0]))
                Template.linearize_array(v[1], a)
        a.append(RecordStates.EXPECT_OBJECT_END)

    @staticmethod
    def linearize_array(t, a):
        for v in t:
            if v is None:
                a.append(RecordStates.EXPECT_LITERAL)
            elif isinstance(v, JSVObjectTemplate):
                a.append(RecordStates.EXPECT_OBJECT_START)
                Template.linearize_object(v, a)
            elif isinstance(v, JSVArrayTemplate):
                a.append(RecordStates.EXPECT_ARRAY_START)
                Template.linearize_array(v, a)
        a.append(RecordStates.EXPECT_ARRAY_END)
