from os import fsdecode
from io import TextIOBase
import re
from jsv.template import JSVTemplate


DEFAULT_TEMPLATE_ID = '_'


def get_template(t):
    if isinstance(t, JSVTemplate):
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

    def __contains__(self, tmpl):
        return get_template(tmpl) in self._template_dict

    def _add(self, tmpl, tid):
        td = self._template_dict

        t = get_template(tmpl)
        if t in td:
            td[t].add(tid)
        else:
            td[t] = {tid}

    def _remove(self, tmpl, tid):
        t = get_template(tmpl)
        td = self._template_dict
        if len(td[t]) > 1:
            td[t].remove(tid)
        else:
            del td[t]


class JSVCollection:
    """Use multiple templates in a single data stream.

    A :class:`.JSVCollection` object is an associative array of templates, each with an id of type str. This facilitates
    reading from and writing to a file or stream, as each line in the file or stream must be matched to a template.

    Args:
        template_dict (dict): A dictionary whose keys are template ids and whose values are :class:`.JSVTemplate`
            objects, or are values suitable for the :class:`.JSVTemplate` constructor.

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
            raise ValueError('Template id `{0}` is not valid. It must match `{1}`'.format(tid, id_regex_str))
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
            raise KeyError(tid)

    def __iter__(self):
        return iter(self._id_dict)

    def __contains__(self, tid):
        return tid in self._id_dict

    def __len__(self):
        return len(self._id_dict)

    def items(self):
        """Iterator that yields the tuple (tid, template)."""
        return self._id_dict.items()

    def template_lines(self):
        """Iterator that yields the string defining a template in a ``.jsv`` file. For example:

            >>> coll = jsv.JSVCollection()
            >>> coll['template_1'] = '{"key_1"}'
            >>> for s in coll.template_lines():
            ...     print(s)
            ...
            #_ {}
            #template_1 {"key_1"}

        See :meth:`get_template_line`
        """
        for tid in self:
            yield self.get_template_line(tid)

    @property
    def templates(self):
        """Object that allows reverse lookup of template id from a given template. For example:

            >>> coll = jsv.JSVCollection()
            >>> coll['template_1'] = '{"key_1"}'
            >>> coll['template_2'] = '{"key_2"}'
            >>> coll.templates['{"key_1"}']
            'template_1'

        Also allows testing for containment with the ``in`` operator:

            >>> '{"key_1"}' in coll.templates
            True
            >>> '{"key_5"}' in coll.templates
            False
        """
        return self._template_keys

    def get_template_line(self, tid=DEFAULT_TEMPLATE_ID):
        """
        Return a string defining a template in a ``.jsv`` file. For example:

            >>> coll = jsv.JSVCollection()
            >>> coll['template_1'] = '{"key_1"}'
            >>> coll.get_template_line('template_1')
            '#template_1 {"key_1"}'

        Args:
            tid (str): The id of the template.
        """
        if not isinstance(tid, str):
            raise TypeError('argument `key` must be a string')

        if tid not in self._id_dict:
            raise KeyError(tid)

        return '#{0} {1}'.format(tid, str(self._id_dict[tid]))

    def get_record_line(self, obj, tid=DEFAULT_TEMPLATE_ID):
        """
        Returns a string defining a record in a ``.jsv`` file. For example:

            >>> coll = jsv.JSVCollection()
            >>> coll['template_1'] = '{"key_1"}'
            >>> coll.get_record_line({'key_1': 'value_1'}, 'template_1')
            '@template_1 {"value_1"}'

        Args:
            obj (json-compatible object): The object to be encoded.
            tid (str): The id of the template.
        """
        if not isinstance(tid, str):
            raise TypeError('argument `key` must be a string')

        if tid not in self._id_dict:
            raise KeyError(tid)

        if tid == DEFAULT_TEMPLATE_ID:
            return self._id_dict[tid].encode(obj)
        else:
            return '@{0} {1}'.format(tid, self._id_dict[tid].encode(obj))

    def read_line(self, line):
        """Used to read a single line from a ``.jsv`` file. For example:

            >>> coll = jsv.JSVCollection()
            >>> tid, tmpl = coll.read_line('#template_1 {"key_1"}')
            >>> coll[tid] = tmpl
            >>> coll.read_line('@template_1 {"value_1"}')
            ('template_1', {'key_1': 'value_1'})

        Args:
            line (str): String to be read. The string should be in the format used by a ``.jsv`` file. It can be either
                a record or a template.

        Returns:
            tuple: (tid, template_or_record)
        """
        char_list = list(reversed(line))
        if char_list[-1] == '@':
            char_list.pop()
            tid = get_tid(char_list)
            obj = self[tid].decode(char_list)
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
    def __init__(self, rec_file, rec_mode, tmpl_file=None, tmpl_mode=None):

        if isinstance(rec_file, TextIOBase):
            self._manage_rec_fp = False
            self._rec_fp = rec_file
            self._rec_path = None
            self._rec_mode = None
        else:
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
        if self._manage_rec_fp:
            self._rec_fp = open(self._rec_path, self._rec_mode)
            if not self._has_tmpl_file:
                self._tmpl_fp = self._rec_fp
        if self._manage_tmpl_fp:
            self._tmpl_fp = open(self._tmpl_path, self._tmpl_mode)

    def exit(self):
        if self._manage_rec_fp:
            self._rec_fp.close()
        if self._manage_tmpl_fp:
            self._tmpl_fp.close()

    @property
    def has_tmpl_file(self):
        return self._has_tmpl_file

    @property
    def manage_rec_fp(self):
        return self._manage_rec_fp

    @property
    def manage_tmpl_fp(self):
        return self._manage_tmpl_fp

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
    """Context manager for writing data to files in JSV format.

    This is the main class for writing JSV records to a file or stream. If either ``record_file`` or ``template_file``
    is a string, then it must be used as a context manager. Otherwise, the context manager does nothing with the file
    pointers, and the object can be used as a context manager or not.

    As :class:`JSVWriter` inherits from :class:`JSVCollection`, it maintains any templates assigned to it. In addition,
    templates are immediately written to the file or stream when added.

    Example:

        >>> out = []
        >>> out.append({'key_1': 1, 'key_2': 2, 'key_3': 3})
        >>> out.append({'key_1': 4, 'key_2': 5, 'key_3': 6})
        >>> out.append({'key_1': 7, 'key_2': 8, 'key_3': 9})
        >>> with jsv.JSVWriter('out.jsv', 'wt', {'_': '{"key_1","key_2","key_3"}'}) as w:
        ...     for obj in out:
        ...         w.write(obj)

    This creates the file ``out.jsv`` which looks like this:

    .. code-block:: text

        #_ {"key_1","key_2","key_3"}
        {1,2,3}
        {4,5,6}
        {7,8,9}

    Args:
        record_file (filepath or :class:`io.TextIOBase`): Either a file path, or a file pointer to which records should
            be written. If ``template_file`` is not given, templates will be written here as well.
        record_mode (str): file mode for the record file. Only used if ``record_file`` is a string.
        template_dict (dict): Dictionary of templates. See :class:`JSVCollection`.
        template_file (filepath or :class:`io.TextIOBase`): Either a file path, or a file pointer to which templates
            should be written. if present, templates and records will be written to different files. By convention,
            records should use the file extension ``.jsvr`` and templates should use file extension ``.jsvt``.
        template_mode (str): file mode for the template file. Only used if ``template_file`` is a string.

    """
    def __init__(self, record_file, record_mode='at', template_dict=None, template_file=None, template_mode='at'):
        super().__init__(template_dict)
        self.files = FileManager(record_file, record_mode, template_file, template_mode)
        if ((self.files.has_tmpl_file and not self.files.manage_tmpl_fp) or
                (not self.files.has_tmpl_file and not self.files.manage_rec_fp)):
            for line in self.template_lines():
                print(line, file=self.files.tmpl_fp)

    def __enter__(self):
        self.files.enter()
        if ((self.files.has_tmpl_file and self.files.manage_tmpl_fp) or
                (not self.files.has_tmpl_file and self.files.manage_rec_fp)):
            for line in self.template_lines():
                print(line, file=self.files.tmpl_fp)
        return self

    def __exit__(self, t, v, tr):
        self.files.exit()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        try:
            if self.files.has_tmpl_file:
                fp = self.files.tmpl_fp
            else:
                fp = self.files.rec_fp
        except RuntimeError:
            fp = None
        if fp:
            print(self.get_template_line(key), file=fp)

    def write(self, obj, tid='_'):
        """Writes an object to a file or stream in JSV format

        Args:
            obj (json-compatible object): Object to be written.
            tid (str): Id of the template used to encode ``obj``.
        """
        if isinstance(obj, JSVTemplate):
            raise ValueError('Cannot use `write` method to write a template. Template is written when added to'
                             'JSVCollection object')
        s = self.get_record_line(obj, tid)
        print(s, file=self.files.rec_fp)


class JSVReader(JSVCollection):
    """Context manager for reading data from files in JSV format.

    This is the main class for reading JSV records from a file or stream. If either ``record_file`` or ``template_file``
    is a string, then it must be used as a context manager. Otherwise, the context manager does nothing with the file
    pointers, and the object can be used directly.

    All of the templates used by a :class:`JSVReader` instance must come from either ``record_file`` or
    ``template_file``. If it is present, ``template_file`` is read during initialization (if ``template_file`` is a file
    pointer) or when entering the context manager (if ``template_file`` is a file path).

    Example:

        Take the file ``in.jsv`` which looks like this:

    .. code-block:: text

        #_ {"key_1","key_2","key_3"}
        {1,2,3}
        {4,5,6}
        {7,8,9}

    We can then run the following code:

        >>> with jsv.JSVReader('in.jsv') as r:
        ...     for obj in r:
        ...         print(obj)
        ...
        {'key_1': 1, 'key_2': 2, 'key_3': 3}
        {'key_1': 4, 'key_2': 5, 'key_3': 6}
        {'key_1': 7, 'key_2': 8, 'key_3': 9}

    Args:
        record_file (filepath or :class:`io.TextIOBase`): Either a file path, or a file pointer from which records
            should be read. Templates, if present, will also be read.
        template_file (filepath or :class:`io.TextIOBase`): Either a file path, or a file pointer to which templates
            should be written. If present, templates and records will be written to different files. By convention,
            records should use the file extension ``.jsvr`` and templates should use file extension ``.jsvt``.
    """
    def __init__(self, record_file, template_file=None):
        super().__init__()
        self._fm = FileManager(record_file, 'rt', template_file, 'rt')
        if self._fm.has_tmpl_file and not self._fm.manage_tmpl_fp:
            populate_from_tmpl_file(self._fm.tmpl_fp, self)

    def __enter__(self):
        self._fm.enter()
        if self._fm.has_tmpl_file and self._fm.manage_tmpl_fp:
            populate_from_tmpl_file(self._fm.tmpl_fp, self)
        return self

    def __exit__(self, t, v, tr):
        self._fm.exit()

    def __iter__(self):
        """Iterator magic method for the reader object. Templates are consumed to decode records, but are not returned
        by the iterator.

        Returns:
            (object) where ``object`` is a json-compatible object representing a record.
        """
        for line in self._fm.rec_fp:
            tid, obj = self.read_line(line)
            if isinstance(obj, JSVTemplate):
                self[tid] = obj
            else:
                yield obj

    def items(self):
        """Iterator over both the values and the template ids for each record. Templates are consumed to decode records,
        but are not returned by the iterator.

        Returns:
             (tid, object) where ``tid`` is the id of the template used, and ``object`` is a json-compatible object.
        """
        for line in self._fm.rec_fp:
            tid, obj = self.read_line(line)
            if isinstance(obj, JSVTemplate):
                self[tid] = obj
            else:
                yield tid, obj


id_regex_str = '[a-zA-Z_0-9]+'
id_re = re.compile(id_regex_str)


def validate_id(id):
    m = id_re.match(id)
    return m.group() == id
