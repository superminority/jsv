from collections import OrderedDict
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
        self._default_template = Template('')

    def __enter__(self):
        self._file_obj = open(self._file_name, self._mode)
        return self

    def __exit__(self, type, value, traceback):
        self._file_obj.close()

    def add_template(self, template, **kwargs):
        if 'id' in kwargs:
            if kwargs['id']
        if 'test' in kwargs:

        if isinstance(template, str):
            t = Template(template)
        elif isinstance(template, Template):
            t = template
        else:
            raise TypeError('`template` must be either a string or a Template object')

        self._templates.update = {id: {
            'template': t,
            'test': test,
            'id': id
        }}

    def write(self, obj, **kwargs):
        if len(kwargs) != 1:
            raise KeyError('Either `template` or `id` keyword argument is required, but not both')
        else:
            if 'template' in kwargs:
                if not isinstance(kwargs['template'], Template):
                    raise TypeError('template must be an object of type Template')

        if id:
            t = self._templates[id]
        else:
            t = self._default_template
            for k, v in self._template.items():
                if v['test'](obj):
                    t = v['template']
                    break
                    
        if id == '_':
            print(t.encode(obj))
        else:
            print('@{0} {1}'.format(id, t.encode(obj)))

