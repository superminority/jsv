from os import fsdecode
from io import TextIOBase
from copy import deepcopy
import re
from jsv.template import JSVTemplate


DEFAULT_TEMPLATE_ID = '_'


def get_template(t, cp=False):
    if isinstance(t, JSVTemplate):
        if cp:
            return deepcopy(t)
        else:
            return t
    else:
        return JSVTemplate(t)


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
    """Class for using multiple templates in a single data stream.

    A :class:`.JSVCollection` object is an associative array of templates, each with an id of type str. This facilitates
    reading from and writing to a file or stream, as each line in the file or stream must be matched to a template.

    Args:
        template_dict (dict): A dictionary whose keys are ids and whose values are :class:`.JSVTemplate` objects, or
            are values suitable for the :class:`.JSVTemplate` constructor.

    """
    def __init__(self, template_dict=None):
        self._id_dict = {}
        if template_dict:
            if isinstance(template_dict, dict):
                for k, v in template_dict.items():
                    if isinstance(v, JSVTemplate):
                        t = v
                    else:
                        t = JSVTemplate(v)
                    self._id_dict[k] = t
            else:
                raise TypeError('parameter `template_dict` must be a dictionary')
        if DEFAULT_TEMPLATE_ID not in self._id_dict:
            self._id_dict[DEFAULT_TEMPLATE_ID] = JSVTemplate()
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
    def template_lines(self):
        for tid in self:
            yield self.get_template_line(tid)

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
            tmpl = JSVTemplate(''.join(reversed(char_list)))
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


class FileManager:
    def __init__(self, rec_file, rec_mode=None, tmpl_file=None, tmpl_mode=None):

        self._cm = False
        if isinstance(rec_file, TextIOBase):
            self._manage_rec_fp = False
            self._rec_fp = rec_file
            self._rec_path = None
            self._rec_mode = None
        else:
            if not rec_mode:
                raise ValueError('rec_mode is required if using a file path for a record file')
            self._manage_rec_fp = True
            self._rec_fp = None
            self._rec_path = fsdecode(rec_file)
            self._rec_mode = rec_mode

        if tmpl_file:
            self._has_tmpl_file = True
            if isinstance(tmpl_file, TextIOBase):
                self._manage_tmpl_fp = False
                self._tmpl_fp = tmpl_file
                self._tmpl_path = None
                self._tmpl_mode = None
            else:
                if not tmpl_mode:
                    raise ValueError('tmpl_mode is required if using a file path for a template file')
                self._manage_tmpl_fp = True
                self._tmpl_fp = None
                self._tmpl_path = fsdecode(tmpl_file)
                self._tmpl_mode = tmpl_mode
        else:
            self._has_tmpl_file = False
            self._manage_tmpl_fp = False
            self._tmpl_path = None
            self._tmpl_mode = None
            if self._manage_rec_fp:
                self._tmpl_fp = None
            else:
                self._tmpl_fp = self._rec_fp

    def enter(self):
        self._cm = True
        if self._manage_rec_fp:
            self._rec_fp = open(self._rec_path, self._rec_mode)
            if not self._has_tmpl_file:
                self._tmpl_fp = self._rec_fp
        if self._manage_tmpl_fp:
            self._tmpl_fp = open(self._tmpl_path, self._tmpl_mode)

    def close_tmpl_file(self):
        if self._manage_tmpl_fp:
            if self._tmpl_fp:
                self._tmpl_fp.close()

    def exit(self):
        self._cm = False
        if self._manage_rec_fp:
            self._rec_fp.close()

    @property
    def cm(self):
        return self._cm

    @property
    def has_tmpl_file(self):
        return self._has_tmpl_file

    @property
    def rec_fp(self):
        if not self._rec_fp:
            raise RuntimeError('No file pointer to a record file. Are you in the context manager?')
        return self._rec_fp

    @property
    def tmpl_fp(self):
        if not self._tmpl_fp:
            raise RuntimeError('No file pointer to a template file. Are you in the context manager?')
        return self._tmpl_fp


def populate_from_tmpl_file(fp, coll):
    for line in fp:
        tid, tmpl = coll.read_line(line)
        if not isinstance(tmpl, JSVTemplate):
            raise RuntimeError('Expecting only template definitions in a template file')
        coll[tid] = tmpl


class JSVWriter(JSVCollection):
    def __init__(self, record_file, record_mode='at', template_dict=None, template_file=None, template_mode='at'):
        super().__init__(template_dict)
        self._fm = FileManager(record_file, record_mode, template_file, template_mode)

    def __enter__(self):
        self._fm.enter()
        for line in self.template_lines:
            if line != '#_ {}':
                print(line, file=self._fm.tmpl_fp)
        return self

    def __exit__(self, t, v, tr):
        self._fm.exit()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self._fm.cm:
            print(self.get_template_line(key), file=self._fm.tmpl_fp)

    def write(self, obj, tid='_'):
        if isinstance(obj, JSVTemplate):
            raise ValueError('Cannot use `write` method to write a template. Template is written when added to'
                             'JSVCollection object')
        s = self.get_record_line(obj, tid)
        print(s, file=self._fm.rec_fp)


class JSVReader(JSVCollection):
    def __init__(self, record_file, template_dict=None, template_file=None):
        super().__init__(template_dict)
        self._fm = FileManager(record_file, 'rt', template_file, 'rt')

    def __enter__(self):
        self._fm.enter()
        if self._fm.has_tmpl_file:
            populate_from_tmpl_file(self._fm.tmpl_fp, self)
        return self

    def __exit__(self, t, v, tr):
        self._fm.exit()

    def __iter__(self):
        for line in self._fm.rec_fp:
            tid, obj_or_tmpl = self.read_line(line)
            if isinstance(obj_or_tmpl, JSVTemplate):
                self[tid] = obj_or_tmpl
            else:
                yield tid, obj_or_tmpl

    def read(self):
        return [obj for _, obj in self]


id_regex_str = '[a-zA-Z_0-9]+'
id_re = re.compile(id_regex_str)


def validate_id(id):
    m = id_re.match(id)
    return m.group() == id
