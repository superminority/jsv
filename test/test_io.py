from jsv import JSVCollection, JSVTemplate, JSVReader, JSVWriter
from io import StringIO
from unittest.mock import MagicMock, patch


def test_basic_collection():
    template_dict = {
        'a': JSVTemplate('{"key_1"}'),
        'b': '[{"key_1"}]',
        'c': {'key_1': None}
    }
    coll = JSVCollection(template_dict)

    # Check that the collection is populated
    assert coll['_'] == JSVTemplate()
    assert coll['a'] == JSVTemplate('{"key_1"}')
    assert coll['b'] == JSVTemplate('[{"key_1"}]')
    assert coll['c'] == JSVTemplate('{"key_1"}')
    assert len(coll) == 4

    # Check the reverse lookup
    assert coll.templates['[{"key_1"}]'] == 'b'
    assert coll.templates[JSVTemplate('{"key_1"}')] == {'a', 'c'}
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
    assert templates == {JSVTemplate(''), JSVTemplate('{"key_1"}'), JSVTemplate('[{"key_1"}]')}

    # Check containment operation on JSVCollection
    assert 'a' in coll
    assert 'b' in coll
    assert 'c' in coll
    assert '_' in coll
    assert 'asdf' not in coll

    # Check containment operation on JSVTemplateKeys class
    assert '{"key_1"}' in coll.templates
    assert JSVTemplate() in coll.templates
    assert [{'key_1': None}] in coll.templates
    assert '{"key_2"}' not in coll.templates

    # replace default template and add new ones
    coll['_'] = JSVTemplate('{"new_default"}')
    coll['d'] = '[{"template_d"}]'
    coll['e'] = [{'template_e': None}]
    assert len(coll) == 6
    assert 'd' in coll
    assert 'e' in coll
    assert '[{"template_d"}]' in coll.templates
    assert JSVTemplate('[{"template_d"}]') in coll.templates
    assert JSVTemplate() not in coll.templates

    # Check the delete operation
    assert coll.templates['{"key_1"}'] == {'a', 'c'}
    del coll['a']
    assert 'a' not in coll
    assert '{"key_1"}' in coll.templates
    assert coll.templates['{"key_1"}'] == 'c'
    del coll['c']
    assert '{"key_1"}' not in coll.templates

    # Check key error on delete of non-existent tid
    try:
        del coll['asdfasdf']
        assert False
    except KeyError as ex:
        assert str(ex) == "'asdfasdf'"

    # Check cannot delete default template
    try:
        del coll['_']
        assert False
    except ValueError as ex:
        assert str(ex) == 'Cannot delete the default template'

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

    try:
        tid = '87sfa&&3773'
        coll[tid] = '{"key_1"}'
        assert False
    except ValueError as ex:
        assert str(ex) == 'Template id `{0}` is not valid. It must match `[a-zA-Z_0-9]+`'.format(tid)

    try:
        _ = JSVCollection('sdf')
        assert False
    except TypeError:
        assert True


def test_get_record_line():
    template_dict = {
        'a': JSVTemplate('{"key_1"}'),
        'b': '[{"key_1"}]',
        'c': {'key_1': None}
    }
    coll = JSVCollection(template_dict)

    assert coll.get_record_line({'key_1': 1, 'key_2': None}, 'a') == '@a {1,"key_2":null}'
    assert coll.get_record_line([{'key_1': 1}, {'key_1': 2}], 'b') == '@b [{1},{2}]'
    assert coll.get_record_line({'key_1': 1, 'key_2': None}, 'c') == '@c {1,"key_2":null}'
    assert coll.get_record_line({'key_1': 1, 'key_2': None}) in {'{"key_1":1,"key_2":null}', '{"key_2":null,"key_1":1}'}

    try:
        coll.get_record_line({'key_1': 1, 'key_2': None}, 3)
    except TypeError as ex:
        assert str(ex) == 'argument `key` must be a string'

    try:
        coll.get_record_line({'key_1': 1, 'key_2': None}, 'sdf')
    except KeyError as ex:
        assert str(ex) == "'sdf'"


def test_get_template_line():
    template_dict = {
        'a': JSVTemplate('{"key_1"}'),
        'b': '[{"key_1"}]',
        'c': {'key_1': None}
    }
    coll = JSVCollection(template_dict)

    assert coll.get_template_line('a') == '#a {"key_1"}'
    assert coll.get_template_line('b') == '#b [{"key_1"}]'
    assert coll.get_template_line('c') == '#c {"key_1"}'
    assert coll.get_template_line('_') == '#_ {}'
    assert coll.get_template_line() == '#_ {}'

    # try passing key that is not a string
    try:
        coll.get_template_line(3)
        assert False
    except TypeError as ex:
        assert str(ex) == 'argument `key` must be a string'

    try:
        coll.get_template_line('dfjkjdfk')
        assert False
    except KeyError as ex:
        assert str(ex) == "'dfjkjdfk'"


def test_read_line():
    coll = JSVCollection()

    assert 'a' not in coll
    tid, tmpl = coll.read_line('#a {"key_1"}')
    assert 'a' in coll
    assert tid == 'a' and tmpl == JSVTemplate('{"key_1"}')

    assert '_' in coll
    assert '{}' in coll.templates
    _, tmpl = coll.read_line('#_ [{"key_1"}]')
    assert tmpl in coll.templates
    assert tmpl == JSVTemplate('[{"key_1"}]')

    tid, rec = coll.read_line('@a {"value"}')
    assert tid == 'a'
    assert rec == {'key_1': 'value'}

    try:
        _, _ = coll.read_line('@* {"value"}')
        assert False
    except ValueError as ex:
        assert str(ex) == 'Template id must match regex `[a-zA-Z_0-9]+`'

    try:
        _, _ = coll.read_line('@ {"value"}')
        assert False
    except ValueError as ex:
        assert str(ex) == 'Template id must not be the empty string'


reader_data = [
    '#_ {"key_1"}',
    '{"record_1"}',
    '{"record_2"}'
]
read_expected = [
    {'key_1': 'record_1'},
    {'key_1': 'record_2'}
]
mock_file = MagicMock(return_value=StringIO('\n'.join(reader_data)))


@patch('builtins.open', mock_file)
def test_jsv_reader():
    with JSVReader('some file') as r:
        for (tid, rec), exp in zip(r.items(), read_expected):
            assert tid == '_'
            assert rec == exp


writer_tmpl = JSVTemplate('{"key_1"}')
writer_recs = [
    {'key_1': 'record_1'},
    {'key_1': 'record_2'}
]
write_expected = {
    'combined': '#_ {"key_1"}\n{"record_1"}\n{"record_2"}\n',
    'template': '#_ {"key_1"}\n',
    'record': '{"record_1"}\n{"record_2"}\n'
}


class StringIOIter:
    def __iter__(self):
        while True:
            yield StringIO()


mock_file = MagicMock(side_effect=StringIOIter())


@patch('builtins.open', mock_file)
def test_jsv_writer():
    with JSVWriter('some file') as w:
        w['_'] = writer_tmpl
        for obj in writer_recs:
            w.write(obj)
        w.files.rec_fp.seek(0)
        out = w.files.rec_fp.read()
        assert out == write_expected['combined']
    with JSVWriter('/some/other/file', 'at', {'_': writer_tmpl}, '/template/file', 'at') as w:
        for obj in writer_recs:
            w.write(obj)
        w.files.rec_fp.seek(0)
        out = w.files.rec_fp.read()
        assert out == write_expected['record']
        w.files.tmpl_fp.seek(0)
        out = w.files.tmpl_fp.read()
        assert out == write_expected['template']
    with StringIO() as f:
        w = JSVWriter(f)
        w['_'] = writer_tmpl
        for obj in writer_recs:
            w.write(obj)
        f.seek(0)
        out = f.read()
        assert out == write_expected['combined']
    with StringIO() as rec_file, StringIO() as tmpl_file:
        w = JSVWriter(rec_file, 'at', {'_': writer_tmpl}, tmpl_file)
        for obj in writer_recs:
            w.write(obj)
        rec_file.seek(0)
        out = rec_file.read()
        assert out == write_expected['record']
        tmpl_file.seek(0)
        out = tmpl_file.read()
        assert out == write_expected['template']



