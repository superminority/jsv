from enum import Enum, auto, unique
from re import compile
from .template import JSVArrayValues, JSVObjectValues


@unique
class States(Enum):
    DONE = auto()
    EXPECT_VALUE_OR_ARRAY_CLOSE = auto()
    EXPECT_VALUE_OR_OBJECT_CLOSE = auto()
    EXPECT_ARRAY_OR_OBJECT = auto()
    ARRAY_NEXT_OR_CLOSE = auto()
    OBJECT_AFTER_KEY = auto()
    OBJECT_NEXT_OR_CLOSE = auto()
    STRING_NEXT_OR_CLOSE = auto()
    STRING_ESCAPE = auto()
    STRING_HEX = auto()
    EXPECT_LITERAL_OR_CLOSE = auto()
    EXPECT_QUOTE = auto()


hex_re = compile('[0-9a-fA-F]')


class RecordDecoder:

    def __init__(self, s):
        self.state = States.EXPECT_ARRAY_OR_OBJECT
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
                    self.current.append(v)
                else:
                    self.current = v
                    self.state = States.DONE
            raise ValueError('Expecting ')
