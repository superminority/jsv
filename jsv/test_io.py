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
    assert coll['_'] == Template()
    assert coll['a'] == Template('{"key_1"}')
    assert coll['b'] == Template('[{"key_1"}]')
    assert coll['c'] == Template('{"key_1"}')
    assert len(coll) == 4

    # replace default template and add new ones
    coll['_'] = Template('{"new_default"}')
    coll['d'] = '[{"template_d"}]'
    coll['e'] = [{'template_e': None}]

    ids = 
