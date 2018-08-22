import pytest
from .template import JSVObjectValues, JSVArrayValues, JSVObjectKeys, JSVArrayDef, JSVDecoder


def test_record_dict():
    rd_values = ["value_1", 2, None]
    rd = JSVObjectValues(*rd_values)
    for v, ex in zip(rd, rd_values):
        assert v == ex
    assert isinstance(rd, JSVObjectValues)


def test_record_list():
    rd_values = ["value_1", 2, None]
    rd = JSVArrayValues(*rd_values)
    for v, ex in zip(rd, rd_values):
        assert v == ex
    assert isinstance(rd, JSVArrayValues)


def test_dict_expand():
    rd_values = ["value_1", 2, None]
    rd = JSVArrayValues(*rd_values)
    rd_keys = ["key_1", "key_2", "key_3"]
    rdk = JSVObjectKeys(*rd_keys)
    dct = rdk.expand(rd)
    for k, v in zip(rd_keys, rd_values):
        assert dct[k] == v


def test_array_expand():
    expected = [
        {"key_1": "value_1_1", "key_2": 21, "key_3": None},
        {"key_1": "value_1_2", "key_2": 22, "key_3": ''},
        {"key_1": "value_1_3", "key_2": 23, "key_3": 0}
    ]
    input = {
        'keys': ["key_1", "key_2", "key_3"],
        'values': JSVArrayValues(*[JSVObjectValues(*dvals.values()) for dvals in expected])
    }

    ad = JSVArrayDef(JSVObjectKeys(*input['keys']))
    assert ad.expand(input['values']) == expected


def test_decode_simple_keys():
    template_string = '{"key_1","key_2","key_3"}'
    expected = JSVObjectKeys('key_1', 'key_2', 'key_3')
    out = JSVDecoder().decode(template_string)
    assert out == expected


def test_decode_simple_array():
    template_string = '[{"key_1","key_2"}]'
    expected = JSVArrayDef(JSVObjectKeys('key_1', 'key_2'))
    out = JSVDecoder().decode(template_string)
    assert out == expected


def test_decode_keys_with_array():
    template_string = '{"key_1","key_2":[{"array_key_1","array_key_2"}]}'
    expected = JSVObjectKeys("key_1", ("key_2", JSVArrayDef(JSVObjectKeys('array_key_1', 'array_key_2'))))
    out = JSVDecoder().decode(template_string)
    assert out == expected

def test_decode_values_with_array():
    template_string = '{"key_1","key_2":[{"array_key_1","array_key_2"}]}'
    template = JSVDecoder().decode(template_string)
    values_string = '{"value_1", "[{"value_1_1", "value_2_1"},{"value_1_2","value_2_2"}]'
    expected = {
        'key_1': 'value_1',
        'key_2': [
            {
                'array_key_1': 'value_1_1',
                'array_key_2': 'value_2_1'
            },
            {
                'array_key_1': 'value_1_2',
                'array_key_2': 'value_2_2'
            }
        ]
    }
    values = JSVObjectValues('value_1', JSVArrayValues(
        JSVObjectValues("value_1_1", "value_2_1"),
        JSVObjectValues("value_1_2", "value_2_2")))
    out = template.expand(values)
    assert out == expected
