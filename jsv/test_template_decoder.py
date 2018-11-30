
from .template_decoder import Template
import pytest


wellformed_db = [
    {
        'template': '[{"key_1"}]',
        'valid_records': [
            {
                'record_string': '[{1}]',
                'object': [{'key_1': 1}]
            },
            {
                'record_string': '[{1},{"two"},{3.0}]',
                'object': [{'key_1': 1}, {'key_1': 'two'}, {'key_1': 3.0}]
            }
        ]
    },
    {
        'template': '[ {  "key_1" \t}\n]'
    },
    {
        'template': '{"key_1":[{"key_2","key_3"}]}',
        'valid_records': [
            {
                'record_string': '{[{"two",3}]}',
                'object': {'key_1': [{'key_2': "two", 'key_3': 3}]}
            },
            {
                'record_string': '{[{"two",3},{4,"five"}],"key_4":{"sub_key":"value"}}',
                'object': {'key_1': [{'key_2': "two", 'key_3': 3}, {'key_2': 4, 'key_3': "five"}],
                             'key_4': {'sub_key': 'value'}}
            }
        ]
    },
    {
        'template': '{"key_1","key_2","key_3","key_4"}',
        'valid_records': [
            {
                'record_string': '{1,2,3,4}',
                'object': {'key_1': 1, 'key_2': 2, 'key_3': 3, 'key_4': 4}
            },
            {
                'record_string': '{1,2,3,4,"key_5":5}',
                'object': {'key_1': 1, 'key_2': 2, 'key_3': 3, 'key_4': 4, 'key_5': 5}
            },
            {
                'record_string': '{1,2,3,4,"key_5":5,"key_6":"six"}',
                'object': {'key_1': 1, 'key_2': 2, 'key_3': 3, 'key_4': 4, 'key_5': 5, 'key_6': 'six'}
            }
        ]
    },
    {
        'template': '{"key_1":{"key_1_1"},"key_2"}'
    },
    {
        'template': '[{"key_1"},]',
        'valid_records': [
            {
                'record_string': '[{"value_1"},3,{"key_2":"value_2"}]',
                'object': [{'key_1': 'value_1'}, 3, {'key_2': 'value_2'}]
            }
        ]
    },
    {
        'template': '[[{"key_1"}]]'
    },
    {
        'template': '[{"k1"},{"k1"}]'
    }
]


malformed = [
    ('{"key_1"', IndexError, 'End of string reached unexpectedly')
]

decode = []
for wf in wellformed_db:
    if 'valid_records' in wf:
        template = wf['template']
        for vr in wf['valid_records']:
            decode.append((template, vr['record_string'], vr['object']))


@pytest.mark.parametrize('template_string, expected', [(s['template'], s['record_states']) for s in wellformed_db])
def test_template_object(template_string, expected):
    obj = Template(template_string)
    assert obj._record_states == expected


@pytest.mark.parametrize('template_string, record_string, expected', decode)
def test_decode(template_string, record_string, expected):
    templ = Template(template_string)
    record = templ.decode(record_string)
    assert record == expected


@pytest.mark.parametrize('template_string, expected, obj', decode)
def test_encode(template_string, expected, obj):
    templ = Template(template_string)
    record_string = templ.encode(obj)
    assert record_string == expected


@pytest.mark.parametrize('template_string, ex, msg', malformed)
def test_template_ex(template_string, ex, msg):
    with pytest.raises(ex, message=msg):
        Template(template_string)
