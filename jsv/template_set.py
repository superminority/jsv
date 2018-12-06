import re
from jsv.template import Template


class TemplateSingleWriter:
    pass


class TemplateMultiWriter:
    def __init__(self, filename, mode='at'):
        self._file_name = filename
        self._mode = mode
        self._template_dict = {}
        self._id_dict = {}
        self._tests = []
        self._default_template = {
            'template': Template(''),
            'written': False,
            'default': True
        }

    def __enter__(self):
        self._file_obj = open(self._file_name, self._mode)
        return self

    def __exit__(self, type, value, traceback):
        self._file_obj.close()

    def add_template(self, template, **kwargs):
        if 'id' in kwargs:
            id = kwargs['id']
            if isinstance(id, str):
                if validate_id(id):
                    new_id = id
                else:
                    raise ValueError('Bad template id. Template id must match `{}`'.format(id_regex_str))
            else:
                raise TypeError('keyword argument `id` must be a string')
        else:
            new_id = get_new_id(self._id_dict)

        if 'default' in kwargs:
            if not isinstance(kwargs['default'], bool):
                raise TypeError('keyword argument `default` must be a boolean')
            elif kwargs['default'] and 'id' in kwargs:
                raise ValueError('keyword argument `default` cannot be true if `id` is provided')
            default = kwargs['default']
        else:
            default = False

        if isinstance(template, Template):
            t = template
        else:
            t = Template(template)

        if default:
            t_obj = {
                'template': t,
                'written': False,
                'default': True
            }
            self._default_template = t_obj
        else:
            t_obj = {
                'id': new_id,
                'template': t,
                'written': False,
                'default': False
            }
            self._id_dict[new_id] = t_obj
        self._template_dict[t] = t_obj

    def write(self, obj, **kwargs):
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
                t_obj = self._default_template
                    
        if t_obj['default']:
            print(t_obj['template'].encode(obj))
        else:
            print('@{0} {1}'.format(t_obj['id'], t_obj['template'].encode(obj)))


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
