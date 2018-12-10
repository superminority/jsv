import pytest
from .io import JSVCollection
from .template import Template


def test_basic_collection():
    template_dict = {
        'a': Template('{"key_1"}'),
        'b': '[{"key_1"}]',
        'c': {'key_1': None}
    }
    coll = JSVCollection(template_dict)

    # Check that the collection is populated
    assert coll['_'] == Template()
    assert coll['a'] == Template('{"key_1"}')
    assert coll['b'] == Template('[{"key_1"}]')
    assert coll['c'] == Template('{"key_1"}')
    assert len(coll) == 4

    # Check the reverse lookup
    assert coll.templates['[{"key_1"}]'] == 'b'
    assert coll.templates[Template('{"key_1"}')] == {'a', 'c'}
    assert coll.templates[''] == '_'

    # Check the operation of JSVCollection as an iterator
    ids = set()
    for i in coll:
        ids.add(i)
    assert ids == {'_', 'a', 'b', 'c'}

    # Check the operation of items() as an iterator
    ids = set()
    templates = set()
    for i, t in coll.items():
        ids.add(i)
        templates.add(t)
    assert ids == {'_', 'a', 'b', 'c'}
    assert templates == {Template(''), Template('{"key_1"}'), Template('[{"key_1"}]')}

    # Check containment operation on JSVCollection
    assert 'a' in coll
    assert 'b' in coll
    assert 'c' in coll
    assert '_' in coll
    assert 'asdf' not in coll

    # Check containment operation on JSVTemplateKeys class
    assert '{"key_1"}' in coll.templates
    assert Template() in coll.templates
    assert [{'key_1': None}] in coll.templates
    assert '{"key_2"}' not in coll.templates

    # replace default template and add new ones
    coll['_'] = Template('{"new_default"}')
    coll['d'] = '[{"template_d"}]'
    coll['e'] = [{'template_e': None}]
    assert len(coll) == 6
    assert 'd' in coll
    assert 'e' in coll
    assert '[{"template_d"}]' in coll.templates
    assert Template('[{"template_d"}]') in coll.templates
    assert Template() not in coll.templates

    # Check the delete operation
    assert coll.templates['{"key_1"}'] == {'a', 'c'}
    del coll['a']
    assert 'a' not in coll
    assert '{"key_1"}' in coll.templates
    assert coll.templates['{"key_1"}'] == 'c'
    del coll['c']
    assert '{"key_1"}' not in coll.templates

    # Check the key errors for ids
    try:
        coll['asdf']
        assert False
    except KeyError:
        assert True

    # Check the templates object key errors
    try:
        coll.templates['{"asdf"}']
        assert False
    except KeyError:
        assert True


def test_get_template_line():
    template_dict = {
        'a': Template('{"key_1"}'),
        'b': '[{"key_1"}]',
        'c': {'key_1': None}
    }
    coll = JSVCollection(template_dict)

    assert coll.get_record_line({'key_1': 1, 'key_2': None}, 'a') == '@a {1,"key_2":null}'
    assert coll.get_record_line([{'key_1': 1}, {'key_1': 2}], 'b') == '@b [{1},{2}]'
    assert coll.get_record_line({'key_1': 1, 'key_2': None}, 'c') == '@c {1,"key_2":null}'
    assert coll.get_record_line({'key_1': 1, 'key_2': None}) == '{"key_1":1,"key_2":null}'

