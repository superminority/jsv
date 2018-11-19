
from .template_decoder import Template, RecordExpectedStates, ParentStates
import pytest


wellformed_db = [
    {
        'template': '[{"key_1"}]',
        'record_states': ((RecordExpectedStates.EXPECT_ARRAY_START,),
                          (RecordExpectedStates.EXPECT_OBJECT_START,),
                          (RecordExpectedStates.EXPECT_VALUE, ParentStates.OBJECT, 'key_1'),
                          (RecordExpectedStates.EXPECT_OBJECT_END, ParentStates.ARRAY),
                          (RecordExpectedStates.EXPECT_ARRAY_END, ParentStates.NONE, 1)),
        'valid_records': [
            {
                'record_string': '[{1}]',
                'expected': [{'key_1': 1}]
            }
        ]
    },
    {
        'template': '[ {  "key_1" \t}\n]',
        'record_states': ((RecordExpectedStates.EXPECT_ARRAY_START,),
                          (RecordExpectedStates.EXPECT_OBJECT_START,),
                          (RecordExpectedStates.EXPECT_VALUE, ParentStates.OBJECT, 'key_1'),
                          (RecordExpectedStates.EXPECT_OBJECT_END, ParentStates.ARRAY),
                          (RecordExpectedStates.EXPECT_ARRAY_END, ParentStates.NONE, 1))
    },
    {
        'template': '{"key_1":[{"key_2","key_3"}]}',
        'record_states': ((RecordExpectedStates.EXPECT_OBJECT_START,),
                          (RecordExpectedStates.EXPECT_ARRAY_START,),
                          (RecordExpectedStates.EXPECT_OBJECT_START,),
                          (RecordExpectedStates.EXPECT_VALUE, ParentStates.OBJECT, 'key_2'),
                          (RecordExpectedStates.EXPECT_COMMA, ParentStates.OBJECT),
                          (RecordExpectedStates.EXPECT_VALUE, ParentStates.OBJECT, 'key_3'),
                          (RecordExpectedStates.EXPECT_OBJECT_END, ParentStates.ARRAY),
                          (RecordExpectedStates.EXPECT_ARRAY_END, ParentStates.OBJECT, 'key_1', 2),
                          (RecordExpectedStates.EXPECT_OBJECT_END, ParentStates.NONE))
    },
    {
        'template': '{"key_1","key_2","key_3","key_4"}',
        'record_states': ((RecordExpectedStates.EXPECT_OBJECT_START,),
                          (RecordExpectedStates.EXPECT_VALUE, ParentStates.OBJECT, 'key_1'),
                          (RecordExpectedStates.EXPECT_COMMA, ParentStates.OBJECT),
                          (RecordExpectedStates.EXPECT_VALUE, ParentStates.OBJECT, 'key_2'),
                          (RecordExpectedStates.EXPECT_COMMA, ParentStates.OBJECT),
                          (RecordExpectedStates.EXPECT_VALUE, ParentStates.OBJECT, 'key_3'),
                          (RecordExpectedStates.EXPECT_COMMA, ParentStates.OBJECT),
                          (RecordExpectedStates.EXPECT_VALUE, ParentStates.OBJECT, 'key_4'),
                          (RecordExpectedStates.EXPECT_OBJECT_END, ParentStates.NONE))
    },
    {
        'template': '{"key_1":{"key_1_1"},"key_2"}',
        'record_states': ((RecordExpectedStates.EXPECT_OBJECT_START,),
                          (RecordExpectedStates.EXPECT_OBJECT_START,),
                          (RecordExpectedStates.EXPECT_VALUE, ParentStates.OBJECT, 'key_1_1'),
                          (RecordExpectedStates.EXPECT_OBJECT_END, ParentStates.OBJECT, 'key_1'),
                          (RecordExpectedStates.EXPECT_COMMA, ParentStates.OBJECT),
                          (RecordExpectedStates.EXPECT_VALUE, ParentStates.OBJECT, 'key_2'),
                          (RecordExpectedStates.EXPECT_OBJECT_END, ParentStates.NONE))
    }
]


malformed = [
    ('{"key_1"', IndexError, 'End of string reached unexpectedly')
]

parse_records = []
for wf in wellformed_db:
    if 'valid_records' in wf:
        template = wf['template']
        for vr in wf['valid_records']:
            parse_records.append((template, vr['record_string'], vr['expected']))


@pytest.mark.parametrize('template_string, expected', [(s['template'], s['record_states']) for s in wellformed_db])
def test_template_object(template_string, expected):
    obj = Template(template_string)
    assert obj._record_states == expected


@pytest.mark.parametrize('template_string, record_string, expected', parse_records)
def test_records(template_string, record_string, expected):
    templ = Template(template_string)
    record = templ.parse_record(record_string)
    assert record == expected




@pytest.mark.parametrize('template_string, ex, msg', malformed)
def test_template_ex(template_string, ex, msg):
    with pytest.raises(ex, message=msg):
        Template(template_string)
