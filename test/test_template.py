from jsv import JSVTemplate, JSVTemplateDecodeError, JSVRecordDecodeError
import pytest


wellformed_db = [
    {
        'template': '{}',
        'template_objects': [
            None,
            {}
        ],
        'alt_templates': [
            '[[]]',
            '[{}]'
        ],
        'valid_records': [
            {
                'record_string': '{"key_1":1}',
                'object': {'key_1': 1}
            }
        ]
    },
    {
        'template': '[{"key_1"}]',
        'template_objects': [
            [{'key_1': None}],
            [{'key_1': {}}],
            [{'key_1': []}]
        ],
        'alt_templates': [
            '[{ "key_1" \t }   \n]',
            '[ {  "key_1" \t}\n]',
            '[{ "key_1" : []}]',
            '[{"key_1"},{"key_1"}]'
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
        ],
        'incompatible_records': [
            {
                'object': {'key_1': 1},
                'error_type': ValueError,
                'error_msg': 'Expecting a list or tuple'
            }
        ]
    },
    {
        'template': '{"key_1":[{"key_2","key_3"}]}',
        'template_objects': [
            {'key_1': [{'key_2': [2, 3, 4], 'key_3': None}, {'key_2': 'value', 'key_3': True}]}
        ],
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
        ],
        'incompatible_records': [
            {
                'object': [{'key_1': 1}],
                'error_type': ValueError,
                'error_msg': 'Expecting a dictionary'
            }
        ]
    },
    {
        'template': '{"key_1","key_2","key_3","key_4"}',
        'alt_templates': [
            '{"key_1"       , "key_2" , "key_3" , "key_4"}'
        ],
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
            },
            {
                'record_string': '{1,,3,}',
                'object': {'key_1': 1, 'key_3': 3}
            },
            {
                'record_string': '{1,2,3,,"key_5":5}',
                'object': {'key_1': 1, 'key_2': 2, 'key_3': 3, 'key_5': 5}
            },
            {
                'record_string': '{"\\\\","\\"","\\b","\\n"}',
                'object': {'key_1': '\\', 'key_2': '"', 'key_3': '\b', 'key_4': '\n'}
            }
        ],
        'invalid_records': [
            ('{1,2,3,,}', JSVRecordDecodeError, 'Expecting `"`: column 8'),
            ('{1,2,3,4,', JSVRecordDecodeError, 'End of string reached unexpectedly while awaiting `"`: column 8'),
            ('{1,2,3,4,"key_5', JSVRecordDecodeError, 'End of string reached unexpectedly: column 14'),
            ('{1,2,3,4,"key_\\h": 5}', JSVRecordDecodeError, 'expecting valid escape character: column 15'),
            ('{1,2,3,4,"key_\\u4t44": 5}', JSVRecordDecodeError, 'Expected a hex character ([0-9A-Fa-f]): column 17')
        ]
    },
    {
        'template': '{"key_1":{"key_1_1"},"key_2"}',
        'alt_templates': [
            '{"key_1":{"key_1_1"}   ,   "key_2"}'
        ],
        'valid_records': [
            {
                'record_string': '{{"1_1"},"2"}',
                'object': {'key_1': {'key_1_1': '1_1'}, 'key_2': '2'}
            }
        ],
        'invalid_records': [
            ('{{"value_1_1"}, ["bad", "json}', JSVRecordDecodeError, 'Error decoding raw json: column 15')
        ]
    },
    {
        'template': '{"key_1":{"key_2":{"key_3"}}}',
        'valid_records': [
            {
                'record_string': '{{{3}}}',
                'object': {'key_1': {'key_2': {'key_3': 3}}}
            }
        ]
    },
    {
        'template': '{"key_1","key_2":{"key_2_1"},"key_3":[{"key_3_1"}]}',
        'valid_records': [
            {
                'record_string': '{1,{2},[{3}]}',
                'object': {'key_1': 1, 'key_2': {'key_2_1': 2}, 'key_3': [{'key_3_1': 3}]}
            },
            {
                'record_string': '{1,{2},[]}',
                'object': {'key_1': 1, 'key_2': {'key_2_1': 2}, 'key_3': []}
            }
        ]
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
        ],
        'invalid_records': [
            ('[{"value_1", "key_2"',
             JSVRecordDecodeError,
             'End of string reached unexpectedly while awaiting `:`: column 19'),
            ('[{"value_1", "key_2" &',
             JSVRecordDecodeError,
             'Expecting `:`: column 21')
        ]
    },
    {
        'template': '[,{"key_1"}]',
        'alt_templates': [
            '[,{ "key_1": {}}]'
        ],
        'valid_records': [
            {
                'record_string': '[3,{"value_1"}]',
                'object': [3, {'key_1': 'value_1'}]
            },
            {
                'record_string': '[3]',
                'object': [3]
            }
        ]
    },
    {
        'template': '[,[{"key_1"}],[{"key_2"}]]',
        'valid_records': [
            {
                'record_string': '[3,[{"value_1"}],[{"value_2"}],[{"value_3"}]]',
                'object': [3, [{'key_1': 'value_1'}], [{'key_2': 'value_2'}], [{'key_2': 'value_3'}]]
            }
        ]
    },
    {
        'template': '[[{"key_1"}]]',
        'template_objects': [
            [[{'key_1': 3}]]
        ],
        'alt_templates': [
            '[[{"key_1"}],[{"key_1"}]]',
            '[[{"key_1"},{"key_1"}]]',
            '[[{"key_1"},{"key_1"}],[{"key_1"},{"key_1"}]]'
        ],
        'valid_records': [
            {
                'record_string': '[[{"value_1"}]]',
                'object': [[{'key_1': 'value_1'}]]
            },
            {
                'record_string': '[[{"value_1"},{"value_2"}]]',
                'object': [[{'key_1': 'value_1'}, {'key_1': 'value_2'}]]
            }
        ],
        'invalid_records': [
            ('', JSVRecordDecodeError, 'End of string reached unexpectedly: column -1'),
            ('{', JSVRecordDecodeError, 'Unexpected character `{` encountered: column 0')
        ]
    },
    {
        'template': '{"\\" \\\\ \\b \\f \\n \\r \\t"}',
        'valid_records': [
            {
                'record_string': '{1}',
                'object': {'" \\ \b \f \n \r \t': 1}
            }
        ]
    },
    {
        'template': '{"\\u0438"}',
        'alt_templates': [
            '{"и"}'
        ],
        'valid_records': [
            {
                'record_string': '{1}',
                'object': {'и': 1}
            }
        ]
    }
]


malformed_template_db = [
    ('{"key_1"', JSVTemplateDecodeError, 'End of string reached unexpectedly: column 7'),
    ('[&', JSVTemplateDecodeError, 'Expecting `{`, `[` or `]`, got `&`: column 1'),
    ('{"key_1":&', JSVTemplateDecodeError, 'Expecting `{` or `[`, got `&`: column 9'),
    ('[{"key_1"} &', JSVTemplateDecodeError, 'Expecting `,` or `]`, got `&`: column 11'),
    ('{"key_1" &', JSVTemplateDecodeError, 'Expecting `,`, `:`, or `}`, got `&`: column 9'),
    ('{"key_1":{"key_2":{"key_3"}} &', JSVTemplateDecodeError, 'Expecting `,` or `}`, got `&`: column 29'),
    ('{&}', JSVTemplateDecodeError, 'Expecting `"`, got `&`: column 1'),
    ('{"key_1', JSVTemplateDecodeError, 'End of string reached unexpectedly: column 6'),
    ('{"key_\\h"}', JSVTemplateDecodeError, 'expecting valid escape character: column 7'),
    ('{"key_\\ua9yt"}', JSVTemplateDecodeError, 'Expected a hex character ([0-9A-Fa-f]): column 10'),
    (1, TypeError, 'Expecting a string, dict, list or None')
]


def copy_lists_with_tuples(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(v, dict) or isinstance(v, list):
                out[k] = copy_lists_with_tuples(v)
            else:
                out[k] = v
    elif isinstance(obj, list):
        out = []
        for v in obj:
            if isinstance(v, dict) or isinstance(v, list):
                out.append(copy_lists_with_tuples(v))
            else:
                out.append(v)
        out = tuple(out)
    else:
        out = obj
    return out


def create_encode_record_list(db):
    arr = []
    for wf in db:
        if 'valid_records' in wf:
            template = wf['template']
            for vr in wf['valid_records']:
                arr.append((template, vr['object'], vr['record_string']))
                arr.append((template, copy_lists_with_tuples(vr['object']), vr['record_string']))
    return arr


# Test well-formed records
@pytest.mark.parametrize('t_str, record, expected', create_encode_record_list(wellformed_db))
def test_encode_record(t_str, record, expected):
    t = JSVTemplate(t_str)
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
    t = JSVTemplate(t_str)
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
    ts = str(JSVTemplate(t_str))
    assert ts == expected


def create_template_equality_list(db):
    arr = []
    for c in db:
        if 'alt_templates' in c:
            ref_template = JSVTemplate(c['template'])
            for t_str in c['alt_templates']:
                arr.append((t_str, ref_template))
    return arr


@pytest.mark.parametrize('t_str, expected', create_template_equality_list(wellformed_db))
def test_template_equality(t_str, expected):
    t = JSVTemplate(t_str)
    assert t == expected


def create_template_nonequality_list(db):
    arr = []
    for i, c in enumerate(db):
        for d in db[i + 1:]:
            arr.append((JSVTemplate(c['template']), JSVTemplate(d['template'])))
    return arr


@pytest.mark.parametrize('t_1, t_2', create_template_nonequality_list(wellformed_db))
def test_template_nonequality(t_1, t_2):
    assert t_1 != t_2


def test_template_nonequality_by_type():
    assert JSVTemplate() != ''


def create_decode_template_from_object_list(db):
    arr = []
    for c in db:
        if 'template_objects' in c:
            ref_template = JSVTemplate(c['template'])
            for obj in c['template_objects']:
                arr.append((obj, ref_template))
                arr.append((copy_lists_with_tuples(obj), ref_template))
    return arr


@pytest.mark.parametrize('obj, expected', create_decode_template_from_object_list(wellformed_db))
def test_decode_template_from_object(obj, expected):
    t = JSVTemplate(obj)
    assert t == expected


def test_type_errors():
    try:
        _ = JSVTemplate(1)
        assert False
    except TypeError as ex:
        assert str(ex) == 'Expecting a string, dict, list or None'

    t = JSVTemplate()
    try:
        t.decode(1)
        assert False
    except TypeError as ex:
        assert str(ex) == 'argument `s` must be a string or a list of characters'


# Test incompatible records
def create_incompatible_record_array(db):
    arr = []
    for c in db:
        if 'incompatible_records' in c:
            t = JSVTemplate(c['template'])
            for ir in c['incompatible_records']:
                arr.append((t, ir['object'], ir['error_type'], ir['error_msg']))
    return arr


@pytest.mark.parametrize('tmpl, obj, err_type, err_msg', create_incompatible_record_array(wellformed_db))
def test_encode_incompatible_record(tmpl, obj, err_type, err_msg):
    try:
        tmpl.encode(obj)
        assert False
    except err_type as ex:
        assert str(ex) == err_msg


def create_decode_incompatible_record_list(db):
    arr = []
    for c in db:
        if 'invalid_records' in c:
            t = JSVTemplate(c['template'])
            for ir in c['invalid_records']:
                arr.append((t,) + ir)
    return arr


@pytest.mark.parametrize('t, rec_str, ex_class, ex_msg', create_decode_incompatible_record_list(wellformed_db))
def test_decode_incompatible_record(t, rec_str, ex_class, ex_msg):
    try:
        t.decode(rec_str)
        assert False
    except ex_class as ex:
        assert ex_msg == str(ex)


# Test Template __init__ exceptions
@pytest.mark.parametrize('t_str, ex_class, ex_msg', malformed_template_db)
def test_template_init_exceptions(t_str, ex_class, ex_msg):
    try:
        JSVTemplate(t_str)
        assert False
    except ex_class as ex:
        assert ex_msg == str(ex)

