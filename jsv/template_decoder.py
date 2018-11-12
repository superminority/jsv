from enum import Enum, auto, unique
from re import compile
import json


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
    EXPECT_QUOTE_OR_OBJECT_CLOSE = auto()
    EXPECT_QUOTE = auto()


@unique
class RecordExpectedStates(Enum):
    EXPECT_OBJECT_START = auto()
    EXPECT_OBJECT_END = auto()
    EXPECT_ARRAY_START = auto()
    EXPECT_ARRAY_END = auto()


@unique
class RecordStates(Enum):
    EXPECT_OBJECT_START = auto()
    EXPECT_NEXT_OBJECT = auto()
    EXPECT_NEXT_OR_OBJECT_END = auto()
    EXPECT_ARRAY_START = auto()
    EXPECT_NEXT_ARRAY = auto()
    EXPECT_NEXT_OR_ARRAY_END = auto()
    EXPECT_VALUE = auto()
    DONE = auto()


@unique
class ParentStates(Enum):
    ARRAY = auto()
    OBJECT = auto()


hex_re = compile('[0-9a-fA-F]')


def json_remainder(s_array):
    print(s_array)
    s = ''.join(reversed(s_array)).lstrip()
    print(s)
    d = json.JSONDecoder()
    v, r = d.raw_decode(s)
    return v, list(reversed(s[r:].lstrip()))


def err_msg(msg, i, c):
    return '{0} @ index: {1}, character: {2}'.format(msg, i, c)


class Template:
    def parse_record(self, s):
        current_char = None
        char_list = list(reversed(s))
        rs = self._record_states
        rs_length = len(rs)
        i = 0
        j = 0
        if rs[j] is RecordExpectedStates.EXPECT_OBJECT_START:
            state = RecordStates.EXPECT_OBJECT_START
        elif rs[j] is RecordExpectedStates.EXPECT_ARRAY_START:
            state = RecordStates.EXPECT_ARRAY_START
        else:
            state = RecordStates.EXPECT_VALUE
        stack = []
        array_def_stack = []

        while state is not RecordStates.DONE:
            try:
                current_char = char_list.pop()
            except IndexError:
                raise IndexError(err_msg('End of string reached unexpectedly', i, current_char))
            i += 1
            print(stack)
            print(state)
            print(''.join(reversed(char_list)))
            print('----------')

            if state is RecordStates.EXPECT_OBJECT_START:
                if current_char.isspace():
                    pass
                elif current_char == '{':
                    stack.append({})
                    j += 1
                    if isinstance(rs[j], str):
                        stack.append(rs[j])
                        j += 1
                        if isinstance(rs[j], str):
                            state = RecordStates.EXPECT_VALUE
                        elif rs[j] is RecordExpectedStates.EXPECT_ARRAY_START:
                            state = RecordStates.EXPECT_ARRAY_START
                    elif rs[j] is RecordExpectedStates.EXPECT_OBJECT_END:
                        state = RecordStates.EXPECT_KEY_OR_OBJECT_END
                else:
                    raise ValueError('Expecting {')

            elif state is RecordStates.EXPECT_NEXT_OBJECT:
                if current_char.isspace():
                    pass
                elif current_char == ',':
                    stack.append(rs[j])
                    j += 1
                    if isinstance(rs[j], str) or rs[j] is RecordExpectedStates.EXPECT_OBJECT_END:
                        state = RecordStates.EXPECT_VALUE
                    elif rs[j] is RecordExpectedStates.EXPECT_OBJECT_START:
                        state = RecordStates.EXPECT_OBJECT_START
                    elif rs[j] is RecordExpectedStates.EXPECT_ARRAY_START:
                        state = RecordStates.EXPECT_ARRAY_START
                else:
                    raise ValueError('Expecting ,')

            elif state is RecordStates.EXPECT_ARRAY_START:
                if current_char.isspace():
                    pass
                elif current_char == '[':
                    stack.append([])
                    j += 1
                    if rs[j] is RecordExpectedStates.EXPECT_ARRAY_END:
                        array_def_stack.append(None)
                        state = RecordStates.EXPECT_VALUE
                    elif rs[j] is RecordExpectedStates.EXPECT_OBJECT_START:
                        array_def_stack.append(j)
                        state = RecordStates.EXPECT_OBJECT_START
                else:
                    raise ValueError('Expecting [')

            elif state is RecordStates.EXPECT_ARRAY_END:
                if current_char.isspace():
                    pass
                elif current_char == ']':
                    array_def_stack.pop()
                    tmp = stack.pop()
                    if stack:
                        if isinstance(stack[-1], list):
                            stack[-1].append(tmp)
                        else:
                            key = stack.pop()
                            stack[-1][key] = tmp
                    else:
                        state = RecordExpectedStates.DONE
                elif current_char == ',':
                    j = array_def_stack[-1]
                    if j is None:
                        state = RecordStates.EXPECT_VALUE
                    elif rs[j] is RecordExpectedStates.EXPECT_ARRAY_START:
                        RecordStates.EXPECT_ARRAY_START
                    elif rs[j] is RecordExpectedStates.EXPECT_OBJECT_START:
                        RecordStates.EXPECT_OBJECT_START

            elif state is RecordStates.EXPECT_OBJECT_END:
                if current_char.isspace():
                    pass
                elif current_char == '}':
                    tmp = stack.pop()
                    key = stack.pop()
                    stack[-1][key] = tmp
                    j += 1
                    if j >= rs_length:
                        out = stack[-1]
                        state = RecordStates.DONE
                    else:
                        tmp = stack.pop()
                        if isinstance(stack[-1], list):
                            stack[-1].append(tmp)
                        else:
                            key = stack.pop()
                            stack[-1][key] = tmp
                        state = rs[j]
                elif current_char == ',':
                    tmp = stack.pop()
                    key = stack.pop()
                    stack[-1][key] = tmp
                    state = RecordStates.EXPECT_QUOTE

        return out

    @property
    def remainder(self):
        return self._remainder

    def __eq__(self, other):
        return self._root == other

    def __init__(self, s):

        if isinstance(s, str):
            state = TemplateStates.EXPECT_ARRAY_OR_OBJECT
            char_list = list(reversed(s))
            parent_stack = []
            record_states = []
            i = -1
            current_char = None

            while state is not TemplateStates.DONE:
                print(state)
                try:

                    current_char = char_list.pop()
                except IndexError:
                    raise IndexError(err_msg('End of string reached unexpectedly', i, current_char))
                i += 1

                # --------------------------------------------
                # State: EXPECT_ARRAY_OR_OBJECT_OR_ARRAY_CLOSE
                # --------------------------------------------
                if state is TemplateStates.EXPECT_ARRAY_OR_OBJECT_OR_ARRAY_CLOSE:
                    if current_char.isspace():
                        pass
                    elif current_char == '{':
                        parent_stack.append(ParentStates.OBJECT)
                        record_states.append(RecordExpectedStates.EXPECT_OBJECT_START)
                        state = TemplateStates.EXPECT_QUOTE_OR_OBJECT_CLOSE
                    elif current_char == '[':
                        parent_stack.append(ParentStates.ARRAY)
                        record_states.append(RecordExpectedStates.EXPECT_ARRAY_START)
                    elif current_char == ']':
                        parent_stack.pop()
                        record_states.append(RecordExpectedStates.EXPECT_ARRAY_END)
                        if parent_stack:
                            if parent_stack[-1] is ParentStates.OBJECT:
                                state = TemplateStates.OBJECT_NEXT_OR_CLOSE
                            else:
                                state = TemplateStates.ARRAY_NEXT_OR_CLOSE
                        else:
                            state = TemplateStates.DONE
                    else:
                        raise ValueError(err_msg('Expecting `{`, `[` or `]`', i, current_char))

                # -----------------------------
                # State: EXPECT_ARRAY_OR_OBJECT
                # -----------------------------
                elif state is TemplateStates.EXPECT_ARRAY_OR_OBJECT:
                    if current_char.isspace():
                        pass
                    elif current_char == '{':
                        parent_stack.append(ParentStates.OBJECT)
                        record_states.append(RecordExpectedStates.EXPECT_OBJECT_START)
                        state = TemplateStates.EXPECT_QUOTE_OR_OBJECT_CLOSE
                    elif current_char == '[':
                        parent_stack.append(ParentStates.ARRAY)
                        record_states.append(RecordExpectedStates.EXPECT_ARRAY_START)
                        state = TemplateStates.EXPECT_ARRAY_OR_OBJECT_OR_ARRAY_CLOSE
                    else:
                        raise ValueError(err_msg('Expecting `{` or `[`', i, current_char))

                # --------------------------
                # State: ARRAY_NEXT_OR_CLOSE
                # --------------------------
                elif state is TemplateStates.ARRAY_NEXT_OR_CLOSE:
                    if current_char.isspace():
                        pass
                    elif current_char == ',':
                        state = TemplateStates.EXPECT_ARRAY_OR_OBJECT
                    elif current_char == ']':
                        parent_stack.pop()
                        record_states.append(RecordExpectedStates.EXPECT_ARRAY_END)
                        if parent_stack:
                            if parent_stack[-1] is ParentStates.OBJECT:
                                state = TemplateStates.OBJECT_NEXT_OR_CLOSE
                            else:
                                state = TemplateStates.ARRAY_NEXT_OR_CLOSE
                        else:
                            state = TemplateStates.DONE
                    else:
                        raise ValueError(err_msg('Expecting `,` or `]`', i, current_char))

                # -----------------------
                # State: OBJECT_AFTER_KEY
                # -----------------------
                elif state is TemplateStates.OBJECT_AFTER_KEY:
                    if current_char.isspace():
                        pass
                    elif current_char == ',':
                        state = TemplateStates.EXPECT_QUOTE
                    elif current_char == ':':
                        state = TemplateStates.EXPECT_ARRAY_OR_OBJECT
                    elif current_char == '}':
                        parent_stack.pop()
                        record_states.append(RecordExpectedStates.EXPECT_OBJECT_END)
                        if parent_stack:
                            if parent_stack[-1] is ParentStates.OBJECT:
                                state = TemplateStates.OBJECT_NEXT_OR_CLOSE
                            else:
                                state = TemplateStates.ARRAY_NEXT_OR_CLOSE
                        else:
                            state = TemplateStates.DONE
                    else:
                        raise ValueError(err_msg('Expecting `,`, `:`, or `}`', i, current_char))

                # ---------------------------
                # State: OBJECT_NEXT_OR_CLOSE
                # ---------------------------
                elif state is TemplateStates.OBJECT_NEXT_OR_CLOSE:
                    if current_char.isspace():
                        pass
                    elif current_char == ',':
                        state = TemplateStates.EXPECT_QUOTE
                    elif current_char == '}':
                        parent_stack.pop()
                        record_states.append(RecordExpectedStates.EXPECT_OBJECT_END)
                        if parent_stack:
                            if parent_stack[-1] is ParentStates.ARRAY:
                                state = TemplateStates.ARRAY_NEXT_OR_CLOSE
                        else:
                            state = TemplateStates.DONE
                    else:
                        raise ValueError(err_msg('Expecting `,` or `}`', i, current_char))

                # ---------------------------
                # State: STRING_NEXT_OR_CLOSE
                # ---------------------------
                elif state is TemplateStates.STRING_NEXT_OR_CLOSE:
                    if current_char == '"':
                        k = ''.join(string_array)
                        record_states.append(k)
                        state = TemplateStates.OBJECT_AFTER_KEY
                    elif current_char == '\\':
                        state = TemplateStates.STRING_ESCAPE
                    else:
                        string_array.append(current_char)

                # --------------------
                # State: STRING_ESCAPE
                # --------------------
                elif state is TemplateStates.STRING_ESCAPE:
                    if current_char == '"':
                        string_array.append('"')
                    elif current_char == '\\':
                        string_array.append('\\')
                    elif current_char == '/':
                        string_array.append('/')
                    elif current_char == 'b':
                        string_array.append('\b')
                    elif current_char == 'f':
                        string_array.append('\f')
                    elif current_char == 'n':
                        string_array.append('\n')
                    elif current_char == 'r':
                        string_array.append('\r')
                    elif current_char == 't':
                        string_array.append('\t')
                    elif current_char == 'u':
                        hex_array = []
                        state = TemplateStates.STRING_HEX
                    else:
                        raise ValueError(err_msg('expecting valid escape character', i, current_char))

                # -----------------
                # State: STRING_HEX
                # -----------------
                elif state is TemplateStates.STRING_HEX:
                    if hex_re.search(current_char):
                        hex_array.append(current_char)
                        if len(hex_array) >= 4:
                            string_array.append(bytearray.fromhex(''.join(hex_array)).decode())
                            state = TemplateStates.STRING_NEXT_OR_CLOSE
                        else:
                            hex_array.append(current_char)
                    else:
                        raise ValueError(err_msg('Expected a hex character ([0-9A-Fa-f])', i, current_char))

                # ----------------------------
                # State: EXPECT_QUOTE_OR_CLOSE
                # ----------------------------
                elif state is TemplateStates.EXPECT_QUOTE_OR_OBJECT_CLOSE:
                    if current_char.isspace():
                        pass
                    elif current_char == '"':
                        string_array = []
                        state = TemplateStates.STRING_NEXT_OR_CLOSE
                    elif current_char == '}':
                        parent_stack.pop()
                        record_states.append(RecordExpectedStates.EXPECT_OBJECT_END)
                        if parent_stack:
                            if parent_stack[-1] is ParentStates.OBJECT:
                                state = TemplateStates.OBJECT_NEXT_OR_CLOSE
                            else:
                                state = TemplateStates.ARRAY_NEXT_OR_CLOSE
                        else:
                            state = TemplateStates.DONE
                    else:
                        raise ValueError(err_msg('Expecting `"` or `}`', i, current_char))

                # -------------------
                # State: EXPECT_QUOTE
                # -------------------
                elif state is TemplateStates.EXPECT_QUOTE:
                    if current_char.isspace():
                        pass
                    elif current_char == '"':
                        string_array = []
                        state = TemplateStates.STRING_NEXT_OR_CLOSE
                    else:
                        raise ValueError('Expecting `"`')
        else:
            raise TypeError('Expecting a string')

        self._remainder = ''.join(reversed(char_list))
        self._record_states = tuple(record_states)
