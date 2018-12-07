from os import fsdecode
from io import TextIOBase
from sys import stdout
import re
from jsv.template import Template


class TemplateReader:
    def __init__(self, fp=None, mode='rt'):
        pass


class TemplateWriter:
    def __init__(self, fp=stdout, **kwargs):
        if isinstance(fp, TextIOBase):
            self._file_obj = fp
            self._external_fp = True
            self._file_name = None
        else:
            self._file_name = fsdecode(fp)
            self._external_fp = False
            self._file_obj = None

        if 'mode' in kwargs:
            self._mode = kwargs['mode']
        else:
            self._mode = 'at'

        self._template_dict = {}
        self._id_dict = {}
        self._tests = []
        self._file_obj = None

        t_obj = {
            'id': '_',
            'template': Template(''),
            'written': False,
            'default': True
        }
        self._id_dict['_'] = t_obj
        self._template_dict[t_obj['template']] = t_obj

        if 'template_dict' in kwargs:
            for k, v in kwargs['template_dict'].items():
                self.add_template(v, id=k)

        if 'template_list' in kwargs:
            for v in kwargs['template_list']:
                self.add_template(v)

        if 'template_fp' in kwargs:
            if isinstance(kwargs['template_fp'], TextIOBase):
                self._file_obj_tmpl = kwargs['template_fp']
                self._ext_tmpl_fp = True
                self._file_name_tmpl = None
                self._mode_tmpl = None
            else:
                self._file_name_tmpl = fsdecode(kwargs['template_fp'])
                self._ext_tmpl_fp = False
                self._file_obj_tmpl = None
                if 'template_mode' in kwargs:
                    self._mode_tmpl = kwargs['template_mode']
                else:
                    self._mode_tmpl = 'at'
            self._has_tmpl_file = True
        else:
            self._has_tmpl_file = False

    def __enter__(self):
        if not self._external_fp:
            self._file_obj = open(self._file_name, self._mode)
        if self._has_tmpl_file:
            if not self._ext_tmpl_fp:
                self._file_obj_tmpl = open(self._file_name_tmpl, self._mode_tmpl)
        return self

    def __exit__(self, type, value, traceback):
        if not self._external_fp:
            self._file_obj.close()
            self._file_obj = None
        if self._has_tmpl_file and not self._ext_tmpl_fp:
            self._file_obj_tmpl.close()
            self._file_obj_tmpl = None

    def add_template(self, template, **kwargs):
        if 'id' in kwargs:
            id = kwargs['id']
            if isinstance(id, str):
                if validate_id(id):
                    new_id = id
                else:
                    raise ValueError(
                        'Bad template id. Template id must match `{}`, and cannot be `_`'.format(id_regex_str))
            else:
                raise TypeError('keyword argument `id` must be a string')
        else:
            new_id = get_new_id(self._id_dict)

        if 'default' in kwargs:
            if not isinstance(kwargs['default'], bool):
                raise TypeError('keyword argument `default` must be a boolean')
            elif kwargs['default'] and 'id' in kwargs:
                if (kwargs['default'] and (new_id != '_')) or ((not kwargs['default']) and (new_id == '_')):
                    raise ValueError('keyword argument `default` and argument `id` are contradictory')
            default = kwargs['default']
        else:
            default = new_id == '_'

        if isinstance(template, Template):
            t = template
        else:
            t = Template(template)

        if default:
            t_obj = {
                'id': '_',
                'template': t,
                'written': False,
                'default': True
            }
            new_id = '_'
        else:
            t_obj = {
                'id': new_id,
                'template': t,
                'written': False,
                'default': False
            }
        self._id_dict[new_id] = t_obj
        self._template_dict[t] = t_obj

        return t_obj['id'], t_obj['template']

    def write(self, obj, **kwargs):
        if not self._file_obj:
            raise RuntimeError('You must be inside the context manager to write')

        if 'template' in kwargs and 'id' in kwargs:
            raise KeyError('Cannot include both `template` and `id` in keyword args')
        else:
            if 'template' in kwargs:
                if isinstance(kwargs['template'], Template):
                    t = kwargs['template']
                else:
                    t = Template(kwargs['template'])
                try:
                    t_obj = self._template_dict[t]
                except KeyError:
                    self.add_template(t)
                    t_obj = self._template_dict[t]
            elif 'id' in kwargs:
                if kwargs['id'] in self._id_dict:
                    t_obj = self._id_dict[kwargs['id']]
                else:
                    raise KeyError('id `{}` not found'.format(kwargs['id']))
            else:
                t_obj = self._id_dict['_']

        if not t_obj['written']:
            if self._has_tmpl_file:
                fp_tmpl = self._file_obj_tmpl
            else:
                fp_tmpl = self._file_obj
            print('#{0} {1}'.format(t_obj['id'], str(t_obj['template'])), file=fp_tmpl)
            t_obj['written'] = True
                    
        if t_obj['default']:
            print(t_obj['template'].encode(obj), file=self._file_obj)
        else:
            print('@{0} {1}'.format(t_obj['id'], t_obj['template'].encode(obj)), file=self._file_obj)

    @property
    def template_dict(self):
        out = {}
        for t_obj in self._id_dict.values():
            out[t_obj['id']] = t_obj['template']

        return out


id_regex_str = '[a-zA-Z_0-9]+'
id_re = re.compile(id_regex_str)


def validate_id(id):
    m = id_re.match(id)
    return m.group() == id


def get_new_id(id_dict):
    i = 0
    while True:
        new_id = str(i)
        if new_id not in id_dict:
            return new_id
        i += 1
