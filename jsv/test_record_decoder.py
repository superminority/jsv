from .template import JSVObjectTemplate, JSVArrayTemplate
from .record_decoder import RecordDecoder, States
import pytest


wellformed = [
    ('"value"', 'value'),
    ('[{"key_1"}]', JSVArrayTemplate(JSVObjectTemplate('key_1'))),
    ('[ {  "key_1" \t}\n]', JSVArrayTemplate(JSVObjectTemplate('key_1'))),
    ('{"key_1":[{"key_2","key_3"}]}',
        JSVObjectTemplate(('key_1', JSVArrayTemplate(JSVObjectTemplate('key_2', 'key_3'))))),
    ('  \r{ "key_1"\t\n:  [ {"key_2"\r,  "key_3"}\r]\t }',
        JSVObjectTemplate(('key_1', JSVArrayTemplate(JSVObjectTemplate('key_2', 'key_3'))))),
    ('{"key_1","key_2","key_3","key_4"}', JSVObjectTemplate('key_1', 'key_2', 'key_3', 'key_4')),
    ('    \t{"key_1"  \n,"key_2", \r"key_3", "key_4"}', JSVObjectTemplate('key_1', 'key_2', 'key_3', 'key_4')),
    ('{"key_1":[[{"key_2","key_3"}]]}',
        JSVObjectTemplate(('key_1', JSVArrayTemplate(JSVArrayTemplate(JSVObjectTemplate('key_2', 'key_3')))))),
]

malformed = [
    ('{"key_1"', ValueError, 'End of string reached unexpectedly')
]


@pytest.mark.parametrize('template_string, expected', wellformed)
def test_decode_template(template_string, expected):
    decoder = RecordDecoder(template_string)
    decoder.advance_all()
    assert decoder.current == expected
    assert decoder.remainder == ''
    assert decoder.state == States.DONE


@pytest.mark.parametrize('template_string, ex, msg', malformed)
def test_exception_template(template_string, ex, msg):
    decoder = RecordDecoder(template_string)
    with pytest.raises(ex, message=msg):
        decoder.advance_all()
