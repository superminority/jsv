from enum import Enum, auto, unique
from re import compile
from .template import JSVArrayValues, JSVObjectValues


@unique
class States(Enum):
    DONE = auto()
    EXPECT_VALUE_OR_ARRAY_CLOSE = auto()
    EXPECT_VALUE_OR_OBJECT_CLOSE = auto()
    EXPECT_ARRAY_OR_OBJECT_OR_VALUE = auto()
    ARRAY_NEXT_OR_CLOSE = auto()
    OBJECT_AFTER_KEY = auto()
    OBJECT_NEXT_OR_CLOSE = auto()
    STRING_NEXT_OR_CLOSE = auto()
    STRING_ESCAPE = auto()
    STRING_HEX = auto()
    NUMBER_EXPECT_DIGIT_AFTER_SIGN = auto()
    NUMBER_EXPECT_DIGIT_OR_DECIMAL_OR_E = auto()
    RAW_EXPECT_RAW_OR_NEXT_OR_CLOSE_ARRAY = auto()
    RAW_EXPECT_RAW_OR_NEXT_OR_CLOSE_OBJECT = auto()
    EXPECT_LITERAL_OR_CLOSE = auto()
    EXPECT_QUOTE = auto()


hex_re = compile('[0-9a-fA-F]')
start_raw_re = compile('[a-zA-Z_]')
mid_raw_re = compile('[a-zA-Z0-9_]')


class StringList(list):
    @property
    def val(self):
        return ''.join(self)


class NumberList(list):
    @property
    def val(self):
        s = ''.join(self)
        try:
            return int(s)
        except ValueError:
            return float(s)


class RawvalueList(list):
    @property
    def val(self):
        return ''.join(self)


class RecordDecoder:

    def __init__(self, s):
        self.state = States.EXPECT_ARRAY_OR_OBJECT_OR_VALUE
        self.char_list = list(reversed(s))
        self.stack = []
        self.current = None
        self.current_char = None

    def advance(self):
        if self.state is States.DONE:
            raise RuntimeError('Cannot advance when state is DONE')
        try:
            self.current_char = self.char_list.pop()
        except IndexError:
            raise ValueError('End of string reached unexpectedly')
        if self.state is States.EXPECT_VALUE_OR_ARRAY_CLOSE:
            if self.current_char.isspace():
                return
            if self.current_char == '"':
                self.current = StringList()
                self.stack.append(self.current)
                self.state = States.STRING_NEXT_OR_CLOSE
                return
            if self.current_char == '+' or self.current_char == '-':
                self.current = NumberList(self.current_char)
                self.stack.append(self.current)
                self.state = States.NUMBER_EXPECT_DIGIT_AFTER_SIGN
            if self.current_char.isdigit():
                self.current = NumberList(self.current_char)
                self.stack.append(self.current)
                self.state = States.NUMBER_EXPECT_DIGIT_OR_DECIMAL_OR_E
            if start_raw_re.search(self.current_char):
                self.current = RawvalueList(self.current_char)
                self.stack.append(self.current)
                self.state = States.RAW_EXPECT_RAW_OR_NEXT_OR_CLOSE_ARRAY
            if self.current_char == '{':
                n = JSVObjectValues()
                self.current = n
                self.stack.append(self.current)
                self.state = States.EXPECT_VALUE_OR_OBJECT_CLOSE
                return
            if self.current_char == '[':
                self.current = JSVArrayValues()
                self.stack.append(self.current)
                return
            if self.current_char == ']':
                v = self.stack.pop()
                if self.stack:
                    self.current = self.stack[-1]
                    if isinstance(self.current, JSVObjectValues):
                        self.state = States.OBJECT_NEXT_OR_CLOSE
                    else:
                        self.state = States.ARRAY_NEXT_OR_CLOSE
                    self.current.append(v)
                else:
                    self.current = v
                    self.state = States.DONE
            raise ValueError('Expecting ')
        if self.state is States.EXPECT_VALUE_OR_OBJECT_CLOSE:
            if self.current_char.isspace():
                return
            if self.current_char == '"':
                self.current = StringList()
                self.stack.append(self.current)
                self.state = States.STRING_NEXT_OR_CLOSE
                return
            if self.current_char == '+' or self.current_char == '-':
                self.current = NumberList(self.current_char)
                self.stack.append(self.current)
                self.state = States.NUMBER_EXPECT_DIGIT_AFTER_SIGN
            if self.current_char.isdigit():
                self.current = NumberList(self.current_char)
                self.stack.append(self.current_char)
                self.state = States.NUMBER_EXPECT_DIGIT_OR_DECIMAL_OR_E
            if start_raw_re.search(self.current_char):
                self.current = RawvalueList(self.current_char)
                self.stack.append(self.current)
                self.state = States.RAW_EXPECT_RAW_OR_NEXT_OR_CLOSE_OBJECT
            if self.current_char == '{':
                n = JSVObjectValues()
                self.current = n
                self.stack.append(self.current)
                return
            if self.current_char == '[':
                self.current = JSVArrayValues()
                self.stack.append(self.current)
                self.state = States.EXPECT_VALUE_OR_ARRAY_CLOSE
                return
            if self.current_char == '}':
                v = self.stack.pop()
                if self.stack:
                    self.current = self.stack[-1]
                    if isinstance(self.current, JSVObjectValues):
                        self.state = States.OBJECT_NEXT_OR_CLOSE
                    else:
                        self.state = States.ARRAY_NEXT_OR_CLOSE
                    self.current.append(v)
                else:
                    self.current = v
                    self.state = States.DONE
            raise ValueError('Expecting ')
        if self.state is States.EXPECT_ARRAY_OR_OBJECT_OR_VALUE:
            if self.current_char.isspace():
                return
            if self.current_char == '"':
                self.current = StringList()
                self.stack.append(self.current)
                self.state = States.STRING_NEXT_OR_CLOSE
                return
