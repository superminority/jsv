from .template import JSVObjectTemplate, JSVArrayTemplate
from .template_decoder import Template
import pytest


wellformed = [
    ('[{"key_1"}]', JSVArrayTemplate(JSVObjectTemplate('key_1'))),
    ('[ {  "key_1" \t}\n]', JSVArrayTemplate(JSVObjectTemplate('key_1'))),
    ('{"key_1":[{"key_2","key_3"}]}',
        JSVObjectTemplate(('key_1', JSVArrayTemplate(JSVObjectTemplate('key_2', 'key_3'))))),
    ('  \r{ "key_1"\t\n:  [ {"key_2"\r,  "key_3"}\r]\t }',
        JSVObjectTemplate(('key_1', JSVArrayTemplate(JSVObjectTemplate('key_2', 'key_3'))))),
    ('{"key_1","key_2","key_3","key_4"}', JSVObjectTemplate('key_1', 'key_2', 'key_3', 'key_4')),
    ('    \t{"key_1"  \n,"key_2", \r"key_3", "key_4"}', JSVObjectTemplate('key_1', 'key_2', 'key_3', 'key_4')),
    ('{"key_1":[[{"key_2","key_3"}]]}',
        JSVObjectTemplate(('key_1', JSVArrayTemplate(JSVArrayTemplate(JSVObjectTemplate('key_2', 'key_3'))))))
   # ('{"key_1":{"key_1_1"},"key_2"}', JSVObjectTemplate('key_1'))
]

malformed = [
    ('{"key_1"', IndexError, 'End of string reached unexpectedly')
]


@pytest.mark.parametrize('template_string, expected', wellformed)
def test_template_object(template_string, expected):
    obj = Template(template_string)
    assert obj._root == expected


@pytest.mark.parametrize('template_string, ex, msg', malformed)
def test_template_ex(template_string, ex, msg):
    with pytest.raises(ex, message=msg):
        Template(template_string)
