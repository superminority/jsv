from enum import Enum, auto, unique
from .template import JSVArrayTemplate, JSVObjectTemplate

@unique
class States(Enum):
    NEW = auto()
    ARRAY_NEXT_OR_CLOSE = auto()
    OBJECT_AFTER_KEY = auto()
    OBJECT_NEXT_OR_CLOSE = auto()
    STRING_NEXT_OR_CLOSE = auto()
    STRING_ESCAPE = auto()
    STRING_HEX = auto()
    EXPECT_QUOTE_OR_CLOSE = auto()
    DONE = auto()

class TemplateDecoder:
    def __init__(self, s):
        self.state = States.NEW
        self.char_list = list(reversed(s))
        self.template = None
        self.stack = []
        self.current = None
        self.char_list = []
        self.current_char = None

    def advance(self):
        if self.state is States.DONE:
            raise RuntimeError('Cannot advance when state is DONE')
        try:
            self.current_char = self.char_list.pop()
        except IndexError:
            raise IndexError('End of string reached unexpectedly')
        if self.state is States.NEW:
            if self.current_char.isspace():
                return
            if self.current_char == '{':
                n = JSVObjectTemplate()
                if self.current and isinstance(self.current, JSVArrayTemplate):
                    self.current.append(n)
                self.current = n
                self.stack.append(self.current)
                self.state = States.EXPECT_QUOTE_OR_CLOSE
                return
            if self.current_char == '[':
                self.current = JSVArrayTemplate()
                self.stack.append(self.current)
                return
            raise ValueError('Expecting ')
        elif self.state is States.ARRAY_NEXT_OR_CLOSE:
            if self.current_char.isspace():
                return
            if self.current_char == ',':
                self.state = States.NEW
            if self.current_char == ']':
                v = self.stack.pop()
                if self.stack:
                    self.current = self.stack[-1]
                    if isinstance(self.current, list):
                        k = ''.join(self.stack.pop())
                        self.current = self.stack[-1]
                        self.current.append((k, v))
                        self.state = States.OBJECT_NEXT_OR_CLOSE
                        return
                    elif isinstance(self.current, JSVArrayTemplate):
                        self.current.append(v)
                        return
                else:
                    self.state = States.DONE
                    return
        elif self.state is States.OBJECT_AFTER_KEY:
            if self.current_char.isspace():
                return
            if self.current_char == ',':
                k = self.current
                self.current = self.stack[-1]
                self.current.append(k)
                self.state = States.NEW
                return
            if self.current_char == ':':
                self.state = States.NEW
                return
            if self.current_char == '}':
                v = self.stack.pop()
                if self.stack:
                    self.current = self.stack[-1]
                    if isinstance(self.current, list):
                        k = ''.join(self.stack.pop())
                        self.current = self.stack[-1]
                        self.current.append((k, v))
                        self.state = States.OBJECT_NEXT_OR_CLOSE
                        return
                    elif isinstance(self.current, JSVArrayTemplate):
                        self.current.append(v)
                        return
                else:
                    self.state = States.DONE
                    return
        elif self.state is States.OBJECT_NEXT_OR_CLOSE:
            if self.current_char.isspace():
                return
            if self.current_char == ',':
                v = self.current
                self.current = self.stack[-1]
                self.current.append(v)
                self.state = States.NEW
                return
            if self.current_char == '}':
                v = self.stack.pop()
                if self.stack:
                    self.current = self.stack[-1]
                    if isinstance(self.current, list):
                        k = ''.join(self.stack.pop())
                        self.current = self.stack[-1]
                        self.current.append((k, v))
                        self.state = States.OBJECT_NEXT_OR_CLOSE
                        return
                    elif isinstance(self.current, JSVArrayTemplate):
                        self.current.append(v)
                        return
                else:
                    self.state = States.DONE
                    return
        elif self.state is States.STRING_NEXT_OR_CLOSE:
            if self.current_char == '"':
                self.state = States.OBJECT_AFTER_KEY
                return
            elif self.current_char == '\\':
                self.state = States.STRING_ESCAPE
                return
            else:
                self.current.append(self.current_char)
                return
        elif self.state is States.STRING_ESCAPE:
            if self.current_char == '"':
                self.current.append('"')
            elif self.current_char == '\\':
                self.current.append('\\')
            elif self.current_char == '/':
                self.current.append('/')
            elif self.current_char == 'b':
                self.current.append('\b')
            elif self.current_char == 'f':
                self.current.append('\f')
            elif self.current_char == 'n':
                self.current.append('\n')
            elif self.current_char == 'r':
                self.current.append('\r')
            elif self.current_char == 't':
                self.current.append('\t')
            elif self.current_char == 'u':
                self.current = []
                self.stack.append(self.current)
                self.state = States.STRING_HEX
        elif self.state is States.STRING_HEX:
            pass