from .template import Template
import pytest


wellformed_db = [
    {
        'template': '[{"key_1"}]',
        'alt_templates': [
            '[{ "key_1" \t }   \n]',
            '[ {  "key_1" \t}\n]',
            '[{ "key_1" : []}]'
        ],
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
        'alt_templates': [
            '[{ "key_1": {}},,,]'
        ],
        'valid_records': [
            {
                'record_string': '[{"value_1"},3,{"key_2":"value_2"}]',
                'object': [{'key_1': 'value_1'}, 3, {'key_2': 'value_2'}]
            }
        ]
    },
    {
        'template': '[[{"key_1"}]]',
        'alt_templates': [
            '[[{"key_1"}],[{"key_1"}]]'
        ]
    },
    {
        'template': '[{"k1"}]',
        'alt_templates': [
            '[{"k1"},{"k1"}]'
        ]
    }
]


malformed = [
    ('{"key_1"', IndexError, 'End of string reached unexpectedly')
]


def create_encode_record_list(db):
    arr = []
    for wf in db:
        if 'valid_records' in wf:
            template = wf['template']
            for vr in wf['valid_records']:
                arr.append((template, vr['object'], vr['record_string']))
    return arr


# Test well-formed records
@pytest.mark.parametrize('t_str, record, expected', create_encode_record_list(wellformed_db))
def test_encode_record(t_str, record, expected):
    t = Template(t_str)
    rs = t.encode(record)
    assert rs == expected


def create_decode_record_list(db):
    arr = []
    for wf in db:
        if 'valid_records' in wf:
            template = wf['template']
            for vr in wf['valid_records']:
                arr.append((template, vr['record_string'], vr['object']))
    return arr


@pytest.mark.parametrize('t_str, rec_str, expected', create_decode_record_list(wellformed_db))
def test_decode_record(t_str, rec_str, expected):
    t = Template(t_str)
    obj = t.decode(rec_str)
    assert obj == expected


def create_encode_template_list(db):
    arr = []
    for c in db:
        ref_template = c['template']
        arr.append((ref_template, ref_template))
        if 'alt_templates' in c:
            for t_str in c['alt_templates']:
                arr.append((t_str, ref_template))
    return arr


# Test well-formed templates
@pytest.mark.parametrize('t_str, expected', create_encode_template_list(wellformed_db))
def test_encode_template(t_str, expected):
    ts = str(Template(t_str))
    assert ts == expected


def test_decode_template_from_string():
    pass


def test_decode_template_from_object():
    pass


# Test incompatible records
def test_encode_incompatible_record():
    pass


def test_decode_incompatible_record():
    pass
