from collections import OrderedDict
from jsv.template import Template


class TemplateWriter:
    def __init__(self, file_name):
        self.file_obj = open(file_name, 'w')
        self._templates = OrderedDict()
        self._default_template = Template('')

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.file_obj.close()

    def add_template(self, template, test, name, id):
        if isinstance(template, str):
            t = Template(template)
        elif isinstance(template, Template):
            t = template
        else:
            raise TypeError('`template` must be either a string or a Template object')

        self._templates.update = {id: {
            'template': t,
            'name': name,
            'test': test,
            'id': id
        }}

    def write(self, obj, id=None):
        if id:
            t = self._templates[id]
        else:
            for k, v in self._template.items():
                if v['test'](obj):
                    t = v['template']
                    
        if id == '_':
            print(t.encode(obj))
        else:
            print('@{0} {1}'.format(id, t.encode(obj)))

