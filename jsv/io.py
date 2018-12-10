from os import fsdecode
from io import TextIOBase
from sys import stdout
from copy import deepcopy
import re
from jsv.template import Template


DEFAULT_TEMPLATE_ID = '_'


def get_template(t, cp=False):
    if isinstance(t, Template):
        if cp:
            return deepcopy(t)
        else:
            return t
    else:
        return Template(t)


class JSVTemplateKeys:
    def __init__(self, id_dict):
        self._template_dict = {}
        for k, v in id_dict.items():
            self._add(v, k)

    def __getitem__(self, tmpl):
        t = get_template(tmpl)
        if t in self._template_dict:
            tid = self._template_dict[t]
            if len(tid) == 1:
                for x in tid:
                    return x
            else:
                return tid
        else:
            raise KeyError(str(t))

    def __iter__(self):
        return iter(self._template_dict)

    def __contains__(self, tmpl):
        return get_template(tmpl) in self._template_dict

    def _add(self, tmpl, tid):
        td = self._template_dict
        if not validate_id(tid):
            raise ValueError('template key must match regex `{}`'.format(id_regex_str))

        t = get_template(tmpl)
        if t in td:
            td[t].add(tid)
        else:
            td[t] = {tid}

    def _remove(self, tmpl, tid):
        t = get_template(tmpl)
        td = self._template_dict
        if t in td:
            if tid in td[t]:
                if len(td[t]) > 1:
                    td[t].remove(tid)
                else:
                    del td[t]
            else:
                raise KeyError(tid)
        else:
            raise KeyError(str(tmpl))


class JSVCollection:
    def __init__(self, template_dict=None):
        self._id_dict = {}
        if template_dict:
            if isinstance(template_dict, dict):
                for k, v in template_dict.items():
                    if isinstance(v, Template):
                        t = v
                    else:
                        t = Template(v)
                    self._id_dict[k] = t
            else:
                raise TypeError('parameter `template_dict` must be a dictionary')
        if DEFAULT_TEMPLATE_ID not in self._id_dict:
            self._id_dict[DEFAULT_TEMPLATE_ID] = Template()
        self._template_keys = JSVTemplateKeys(self._id_dict)

    def __getitem__(self, tid):
        if tid in self._id_dict:
            return self._id_dict[tid]
        else:
            raise KeyError(tid)

    def __setitem__(self, tid, tmpl):
        if not validate_id(tid):
            raise ValueError('`{}` is not a valid')
        t = get_template(tmpl)

        if tid in self._id_dict:
            self._template_keys._remove(self._id_dict[tid], tid)
        self._id_dict[tid] = t
        self._template_keys._add(t, tid)

    def __delitem__(self, tid):
        if tid == DEFAULT_TEMPLATE_ID:
            raise ValueError('Cannot delete the default template')
        if tid in self._id_dict:
            self._template_keys._remove(self._id_dict[tid], tid)
            del self._id_dict[tid]
        else:
            KeyError(tid)

    def __iter__(self):
        return iter(self._id_dict)

    def __contains__(self, tid):
        return tid in self._id_dict

    def __len__(self):
        return len(self._id_dict)

    def items(self):
        return self._id_dict.items()

    @property
    def templates(self):
        return self._template_keys

    def get_template_line(self, tid=DEFAULT_TEMPLATE_ID):
        if not isinstance(tid, str):
            raise TypeError('argument `key` must be a string')

        if tid not in self._id_dict:
            raise KeyError(tid)

        return '#{0} {1}'.format(tid, str(self._id_dict[tid]))

    def get_record_line(self, obj, tid=DEFAULT_TEMPLATE_ID):
        if not isinstance(tid, str):
            raise TypeError('argument `key` must be a string')

        if tid not in self._id_dict:
            raise KeyError(tid)

        if tid == DEFAULT_TEMPLATE_ID:
            return self._id_dict[tid].encode(obj)
        else:
            return '@{0} {1}'.format(tid, self._id_dict[tid].encode(obj))

    def read_line(self, s):
        char_list = list(reversed(s))
        if char_list[-1] == '@':
            char_list.pop()
            tid = get_tid(char_list)
            obj = self[tid].decode(s)
            return tid, obj
        elif char_list[-1] == '#':
            char_list.pop()
            tid = get_tid(char_list)
            tmpl = Template(''.join(reversed(char_list)))
            self[tid] = tmpl
            return tid, tmpl
        else:
            return DEFAULT_TEMPLATE_ID, self._id_dict[DEFAULT_TEMPLATE_ID].decode(char_list)


def get_tid(char_list):
    out_arr = []
    curr_char = char_list.pop()
    while not curr_char == ' ':
        if curr_char.isalpha() or curr_char.isdigit() or curr_char == '_':
            out_arr.append(curr_char)
        else:
            raise ValueError('Template id must match regex `{}`'.format(id_regex_str))
        curr_char = char_list.pop()
    out = ''.join(out_arr)
    if out == '':
        raise ValueError('Template id must not be the empty string')

    return out


class JSVReader(JSVCollection):
    def __init__(self, template_dict=None, **kwargs):
        super().__init__(template_dict)

    def __iter__(self):
        pass

    def get_collection(self):
        return deepcopy(self._coll)

    def read(self):
        pass


class JSVWriter:
    def __init__(self, jsv_collection, **kwargs):
        self._coll = deepcopy(jsv_collection)

    @property
    def collection(self):
        return self._coll

    def write(self, obj):
        pass


id_regex_str = '[a-zA-Z_0-9]+'
id_re = re.compile(id_regex_str)


def validate_id(id):
    m = id_re.match(id)
    return m.group() == id
