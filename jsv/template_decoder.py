from enum import Enum, auto, unique
from re import compile
import json

from .template import JSVArrayTemplate, JSVObjectTemplate


@unique
class States(Enum):
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


hex_re = compile('[0-9a-fA-F]')


def json_remainder(s):
    d = json.JSONDecoder()
    v, r = d.raw_decode(s)
    return v, s[r:].lstrip()


class TemplateDecoder:

    def __init__(self, s):
        self.state = States.EXPECT_ARRAY_OR_OBJECT
        self.char_list = list(reversed(s))
        self.stack = []
        self.current = None
        self.current_char = None

    def expect_object(self, rec, template, parent):
        rem = rec
        if rem[0] != '{':
            raise ValueError('Expecting object')
        rem = rem[1:].lstrip()
        for i, k in enumerate(template):
            if i != 0:
                if rem[0] != ',':
                    raise ValueError('Expecting `,`')
                rem = rem[1:].lstrip()
            if isinstance(k, str):
                obj, rem = json_remainder(rem)
                parent[k] = obj
            elif isinstance(k[1], JSVObjectTemplate):
                parent[k[0]], rem = self.expect_object(rem, k[1], {})
            elif isinstance(k[1], JSVArrayTemplate):
                parent[k[0]], rem = self.expect_array(rem, k[1], [])
        if rem[0] != '}':
            raise ValueError('Expecting `}`')
        return parent, rem[1:].lstrip()

    def expect_array(self, rec, template, parent):
        rem = rec
        if rem[0] != '[':
            raise ValueError('Expecting `[`')
        rem = rem[1:].lstrip()
        k_iter = iter(template)
        k = None
        after_first = True
        cont_iter = True
        while rem[0] != ']':
            if cont_iter:
                try:
                    k = next(k_iter)
                except StopIteration:
                    cont_iter = False
            if after_first:
                if rem[0] != ',':
                    raise ValueError('Expecting `,`')
                rem = rem[1:].lstrip()
                after_first = False
            if k is None:
                tmp, rem = json_remainder(rem)
            if isinstance(k, JSVObjectTemplate):
                tmp, rem = self.expect_object(rem, k, {})
                parent.append(tmp)
            if isinstance(k, JSVArrayTemplate):
                tmp, rem = self.expect_array(rem, k, [])
                parent.append(tmp)
        return parent, rem[1:].lstrip()

    def parse_record(self, rec):
        remainder = rec.lstrip()
        template = self.current
        if template is None:
            return json.dumps(rec)
        if isinstance(template, JSVObjectTemplate):
            return self.expect_object(remainder, template, {})
        if isinstance(template, JSVArrayTemplate):
            return self.expect_array(remainder, template, [])

    def advance_all(self):
        while self.state is not States.DONE:
            print('current char: {0}, state: {1}'.format(self.current_char, str(self.state)))
            print(self.stack)
            self.advance()
        print('current char: {0}, state: {1}'.format(self.current_char, str(self.state)))
        print(self.stack)
        if self.state is not States.DONE:
            raise ValueError('Reached end of string before end of template')

    @property
    def remainder(self):
        return ''.join(reversed(self.char_list))

    def advance(self):
        if self.state is States.DONE:
            raise RuntimeError('Cannot advance when state is DONE')
        try:
            self.current_char = self.char_list.pop()
        except IndexError:
            raise ValueError('End of string reached unexpectedly')
        if self.state is States.EXPECT_ARRAY_OR_OBJECT_OR_ARRAY_CLOSE:
            if self.current_char.isspace():
                return
            if self.current_char == '{':
                n = JSVObjectTemplate()
                self.current = n
                self.stack.append(self.current)
                self.state = States.EXPECT_QUOTE_OR_CLOSE
                return
            if self.current_char == '[':
                self.current = JSVArrayTemplate()
                self.stack.append(self.current)
                return
            if self.current_char == ']':
                v = self.stack.pop()
                if self.stack:
                    self.current = self.stack[-1]
                    if isinstance(self.current, str):
                        k = self.stack.pop()
                        self.current = self.stack[-1]
                        self.current.append((k, v))
                        self.state = States.OBJECT_NEXT_OR_CLOSE
                        return
                    elif isinstance(self.current, JSVArrayTemplate):
                        self.current.append(v)
                        return
                else:
                    self.current = v
                    self.state = States.DONE
            raise ValueError('Expecting ')
        if self.state is States.EXPECT_ARRAY_OR_OBJECT:
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
                self.state = States.EXPECT_ARRAY_OR_OBJECT_OR_ARRAY_CLOSE
                return
            raise ValueError('Expecting ')
        elif self.state is States.ARRAY_NEXT_OR_CLOSE:
            if self.current_char.isspace():
                return
            if self.current_char == ',':
                self.state = States.EXPECT_ARRAY_OR_OBJECT
            if self.current_char == ']':
                v = self.stack.pop()
                if self.stack:
                    self.current = self.stack[-1]
                    if isinstance(self.current, str):
                        k = self.stack.pop()
                        self.current = self.stack[-1]
                        self.current.append((k, v))
                        self.state = States.OBJECT_NEXT_OR_CLOSE
                        return
                    elif isinstance(self.current, JSVArrayTemplate):
                        self.current.append(v)
                        return
                else:
                    self.current = v
                    self.state = States.DONE
                    return
        elif self.state is States.OBJECT_AFTER_KEY:
            if self.current_char.isspace():
                return
            if self.current_char == ',':
                k = self.stack.pop()
                self.current = self.stack[-1]
                self.current.append(k)
                self.state = States.EXPECT_QUOTE
                return
            if self.current_char == ':':
                self.state = States.EXPECT_ARRAY_OR_OBJECT
                return
            if self.current_char == '}':
                k = self.stack.pop()
                v = self.stack.pop()
                v.append(k)
                if self.stack:
                    self.current = self.stack[-1]
                    if isinstance(self.current, str):
                        k2 = self.stack.pop()
                        self.current = self.stack[-1]
                        self.current.append((k2, v))
                    else:
                        self.current.append(v)
                    if isinstance(self.current, JSVObjectTemplate):
                        self.state = States.OBJECT_NEXT_OR_CLOSE
                    else:
                        self.state = States.ARRAY_NEXT_OR_CLOSE
                    return
                else:
                    self.current = v
                    self.state = States.DONE
                    return
        elif self.state is States.OBJECT_NEXT_OR_CLOSE:
            if self.current_char.isspace():
                return
            if self.current_char == ',':
                v = self.current
                self.current = self.stack[-1]
                self.current.append(v)
                self.state = States.EXPECT_ARRAY_OR_OBJECT
                return
            if self.current_char == '}':
                v = self.stack.pop()
                if self.stack:
                    self.current = self.stack[-1]
                    if isinstance(self.current, str):
                        k = self.stack.pop()
                        self.current = self.stack[-1]
                        self.current.append((k, v))
                        return
                    elif isinstance(self.current, JSVArrayTemplate):
                        self.current.append(v)
                        self.state = States.ARRAY_NEXT_OR_CLOSE
                        return
                else:
                    self.state = States.DONE
                    return
        elif self.state is States.STRING_NEXT_OR_CLOSE:
            if self.current_char == '"':
                v = self.stack.pop()
                self.stack.append(''.join(v))
                self.current = self.stack[-1]
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
            return
        elif self.state is States.STRING_HEX:
            if hex_re.search(self.current_char):
                self.current.append(self.current_char)
                if len(self.current) >= 4:
                    v = self.stack.pop()
                    self.current = self.stack[-1]
                    self.current.append(bytearray.fromhex(''.join(v)).decode())
                    self.state = States.STRING_NEXT_OR_CLOSE
                else:
                    self.current.append(self.current_char)
                return
            else:
                raise ValueError('Expected a hex character ([0-9A-Fa-f]), got {}'.format(self.current_char))
        elif self.state is States.EXPECT_QUOTE_OR_CLOSE:
            if self.current_char.isspace():
                return
            if self.current_char == '"':
                self.current = []
                self.stack.append(self.current)
                self.state = States.STRING_NEXT_OR_CLOSE
                return
            if self.current_char == '}':
                v = self.stack.pop()
                if self.stack:
                    self.current = self.stack[-1]
                    if isinstance(self.current, str):
                        k = self.stack.pop()
                        self.current = self.stack[-1]
                        self.current.append((k, v))
                        self.state = States.OBJECT_NEXT_OR_CLOSE
                    elif isinstance(self.current, JSVArrayTemplate):
                        self.current.append(v)
                        self.state = States.ARRAY_NEXT_OR_CLOSE
                    return
                else:
                    self.state = States.DONE
                    return
        elif self.state is States.EXPECT_QUOTE:
            if self.current_char.isspace():
                return
            if self.current_char == '"':
                self.current = []
                self.stack.append(self.current)
                self.state = States.STRING_NEXT_OR_CLOSE
                return
