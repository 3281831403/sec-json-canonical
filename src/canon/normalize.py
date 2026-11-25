"""Deterministic JSON canonicalization primitives.

Parsed documents are serialized to compact, byte-stable UTF-8 per the
contract in README.md: rejected duplicate keys, code-point key ordering
(recursive through arrays), canonical numbers, explicit control-character
escapes and independent batch processing.
"""
import hashlib
import hmac
import json
import math

def _reject_duplicate_keys(pairs):
    seen = set()
    for key, _value in pairs:
        if key in seen:
            raise ValueError("duplicate object key: %r" % (key,))
        seen.add(key)
    return dict(pairs)


def _reject_constant(value):
    raise ValueError("invalid JSON constant: %s" % (value,))


def parse(text):
    """Parse a JSON document.

    Object keys must be strings and duplicate keys at any nesting depth must
    raise ValueError.  Non-finite JSON extensions such as NaN and Infinity are
    rejected as well.
    """
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    return json.loads(
        text,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_constant,
    )


def sort_keys(value):
    """Return a copy with object keys sorted by Unicode code point.

    Sorting is recursive through objects and arrays.  Array element order is
    preserved.  Scalar values are returned unchanged.
    """
    if isinstance(value, dict):
        return {
            key: sort_keys(value[key])
            for key in sorted(value.keys())
        }
    if isinstance(value, list):
        return [sort_keys(item) for item in value]
    return value

def _strip_decimal_zero_fraction(text):
    """Remove redundant trailing zeros after a decimal point."""
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def number_text(value):
    """Return the canonical decimal text for an int or float.

    Integers use plain base ten with no decimal point and no exponent.
    Floats use the shortest round-tripping decimal form, remove a redundant
    fractional zero, use a lowercase exponent without a plus sign or leading
    exponent zero, and map both signed zeros to zero.  Non-finite values are
    rejected.
    """
    if isinstance(value, bool):
        raise TypeError("boolean is not a JSON number")
    if isinstance(value, int):
        return str(value)
    if not isinstance(value, float):
        raise TypeError("expected int or float, got %s" % type(value).__name__)
    if not math.isfinite(value):
        raise ValueError("non-finite numbers are not valid JSON")
    # Collapses both +0.0 and -0.0 to the same canonical text.
    if value == 0:
        return "0"

    text = repr(value)
    if "e" in text or "E" in text:
        mantissa, exponent = text.replace("E", "e").split("e", 1)
        mantissa = _strip_decimal_zero_fraction(mantissa)
        exp_sign = ""
        if exponent[:1] in "+-":
            if exponent[0] == "-":
                exp_sign = "-"
            exponent = exponent[1:]
        exponent = exponent.lstrip("0") or "0"
        return "%se%s%s" % (mantissa, exp_sign, exponent)
    return _strip_decimal_zero_fraction(text)


def escape_string(value):
    """Escape the contents of a JSON string without adding outer quotes.

    Only the quote, the backslash, and C0 control characters are escaped.
    Every C0 control character becomes a lowercase four-digit hexadecimal
    escape.  Non-ASCII characters stay as literal Unicode text.
    """
    pieces = []
    for ch in value:
        code = ord(ch)
        if ch == '"':
            pieces.append('\\"')
        elif ch == "\\":
            pieces.append("\\\\")
        elif code <= 0x1F:
            pieces.append("\\u%04x" % code)
        else:
            pieces.append(ch)
    return "".join(pieces)

def _emit(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return '"' + escape_string(value) + '"'
    if isinstance(value, int):
        return number_text(value)
    if isinstance(value, float):
        return number_text(value)
    if isinstance(value, dict):
        entries = []
        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise TypeError("object keys must be strings")
            entries.append(
                '"' + escape_string(key) + '":' + _emit(value[key])
            )
        return "{" + ",".join(entries) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_emit(item) for item in value) + "]"
    raise TypeError("cannot canonicalize value of type %s" % type(value).__name__)


def canonicalize(value):
    """Serialize a parsed JSON value to compact canonical UTF-8 bytes."""
    return _emit(value).encode("utf-8")


def digest(canonical):
    """Return the lowercase SHA-256 hex digest of canonical bytes."""
    if not isinstance(canonical, bytes):
        raise TypeError("digest only accepts bytes")
    return hashlib.sha256(canonical).hexdigest()


def verify(text, expected_digest):
    """Verify a JSON document against an expected SHA-256 digest.

    Any parsing, normalization, type, or comparison error is reported as a
    failed verification instead of being allowed to escape.
    """
    try:
        actual_digest = digest(canonicalize(parse(text)))
        if not isinstance(expected_digest, str):
            return False
        return hmac.compare_digest(actual_digest, expected_digest)
    except Exception:
        return False


def canon_batch(documents, policy):
    """Canonicalize an iterable of JSON documents independently.

    Policy is either canonical or digest.  The result maps each zero-based
    document index to canonical bytes or to its lowercase SHA-256 hex digest.
    A document must never affect how another document is normalized.
    """
    if policy == "canonical":
        return {
            index: canonicalize(parse(document))
            for index, document in enumerate(documents)
        }
    if policy == "digest":
        return {
            index: digest(canonicalize(parse(document)))
            for index, document in enumerate(documents)
        }
    raise ValueError("unknown batch policy: %r" % (policy,))
