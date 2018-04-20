from .template import RecordDict, RecordList, KeyList, ArrayDef


def test_record_dict():
    rd_values = ["value_1", 2, None]
    rd = RecordDict(*rd_values)
    for v, ex in zip(rd, rd_values):
        assert v == ex
    assert isinstance(rd, RecordDict)


def test_record_list():
    rd_values = ["value_1", 2, None]
    rd = RecordList(*rd_values)
    for v, ex in zip(rd, rd_values):
        assert v == ex
    assert isinstance(rd, RecordList)


def test_dict_expand():
    rd_values = ["value_1", 2, None]
    rd_keys = ["key_1", "key_2", "key_3"]
    rd = RecordList(*rd_values)
    rdk = KeyList(*rd_keys)
    dct = rdk.expand(rd)
    for k, v in zip(rd_keys, rd_values):
        assert dct[k] == v
