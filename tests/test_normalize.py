import pytest

from canon.normalize import (
    canon_batch,
    canonicalize,
    escape_string,
    number_text,
    parse,
    sort_keys,
)


def test_defect_01_duplicate_keys_are_rejected_not_overwritten():
    with pytest.raises(ValueError):
        parse('{"a":1,"\\u0061":2}')


def test_defect_02_object_keys_use_code_point_order_not_length():
    ordered = sort_keys({"b": 2, "aa": 1})
    assert list(ordered.keys()) == ["aa", "b"]


def test_defect_03_objects_inside_arrays_are_sorted():
    ordered = sort_keys({"items": [{"b": 1, "a": 2}, {"d": 3, "c": 4}]})
    keys = [list(item.keys()) for item in ordered["items"]]
    assert keys == [["a", "b"], ["c", "d"]]


def test_defect_04_integers_never_use_exponent_notation():
    for value in (0, 9, 10, 99, 100, 2500, 10**30):
        assert number_text(value) == str(value)


def test_defect_05_negative_zero_is_normalized_to_zero():
    assert number_text(-0.0) == "0"
    assert number_text(0.0) == number_text(-0.0)


def test_defect_06_float_text_keeps_shortest_round_trip_precision():
    assert number_text(1.2345678901234567) == "1.2345678901234567"
    assert number_text(2.2250738585072014e-308) == "2.2250738585072014e-308"


def test_defect_07_non_ascii_characters_are_not_escaped():
    assert escape_string("caf\u00e9\u4e2d\u03a9") == "caf\u00e9\u4e2d\u03a9"


def test_defect_08_every_control_character_uses_lowercase_hex():
    value = "\t\b\r\x00\x1f\n"
    expected = "\\u0009\\u0008\\u000d\\u0000\\u001f\\u000a"
    assert escape_string(value) == expected


def test_defect_09_canonical_output_has_no_trailing_whitespace():
    source = '{ "b" : 2, "a" : [ 1, 3 ] }'
    indented = '{\n  "b": 2,\n  "a": [1, 3]\n}'
    expected = b'{"a":[1,3],"b":2}'
    compact = canonicalize(parse(source))
    pretty = canonicalize(parse(indented))
    assert type(compact) is bytes
    assert compact == expected
    assert pretty == expected
    assert not compact.endswith(b" ")


def test_defect_10_batch_second_document_uses_its_own_key_order():
    documents = ['{"b":2,"a":1}', '{"a":9,"b":8}']
    batched = canon_batch(documents, "canonical")
    assert batched[1] == canonicalize(parse(documents[1]))


def test_key_order_variants_are_byte_identical():
    documents = [
        '{"z":1,"aa":2,"m":3}',
        '{"m":3,"z":1,"aa":2}',
    ]
    expected = b'{"aa":2,"m":3,"z":1}'
    first = canonicalize(parse(documents[0]))
    second = canonicalize(parse(documents[1]))
    assert first == expected
    assert second == expected
    assert first == second


def test_integer_and_equivalent_exponent_are_byte_identical():
    plain = '{"n":100,"m":-7}'
    exponent = '{"n":1E+2,"m":-7.0E0}'
    expected = b'{"m":-7,"n":100}'
    plain_bytes = canonicalize(parse(plain))
    exponent_bytes = canonicalize(parse(exponent))
    assert plain_bytes == expected
    assert exponent_bytes == expected
    assert plain_bytes == exponent_bytes


def test_negative_zero_and_zero_are_byte_identical():
    positive = '{"v":0,"w":0.0}'
    negative = '{"v":-0,"w":-0.0}'
    expected = b'{"v":0,"w":0}'
    positive_bytes = canonicalize(parse(positive))
    negative_bytes = canonicalize(parse(negative))
    assert positive_bytes == expected
    assert negative_bytes == expected
    assert positive_bytes == negative_bytes


def test_duplicate_key_document_is_rejected():
    with pytest.raises(ValueError):
        parse('{"outer":{"x":1,"x":2}}')


def test_two_batches_match_individual_canonicalization():
    documents = [
        '{"b":2,"a":1}',
        '{"a":9,"b":8}',
        '{"b":6,"a":5}',
    ]
    expected = {
        index: canonicalize(parse(document))
        for index, document in enumerate(documents)
    }
    first = canon_batch(documents, "canonical")
    second = canon_batch(documents, "canonical")
    assert first == expected
    assert second == expected