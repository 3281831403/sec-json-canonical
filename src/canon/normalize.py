"""Deterministic JSON canonicalization primitives.

The public contract is described by the docstrings below.  The current
implementation is intentionally non-canonical in several places.
"""
import hashlib
import hmac
import json
import math

def parse(text):
    """Parse a JSON document.

    Object keys must be strings and duplicate keys at any nesting depth must
    raise ValueError.  Non-finite JSON extensions such as NaN and Infinity are
    rejected as well.
    """
    raise NotImplementedError()

def sort_keys(value):
    """Return a copy with object keys sorted by Unicode code point.

    Sorting is recursive through objects and arrays.  Array element order is
    preserved.  Scalar values are returned unchanged.
    """
    raise NotImplementedError()

def number_text(value):
    """Return the canonical decimal text for an int or float.

    Integers use plain base ten with no decimal point and no exponent.
    Floats use the shortest round-tripping decimal form, remove a redundant
    fractional zero, use a lowercase exponent without a plus sign or leading
    exponent zero, and map both signed zeros to zero.  Non-finite values are
    rejected.
    """
    raise NotImplementedError()

def escape_string(value):
    """Escape the contents of a JSON string without adding outer quotes.

    Only the quote, the backslash, and C0 control characters are escaped.
    Every C0 control character becomes a lowercase four-digit hexadecimal
    escape.  Non-ASCII characters stay as literal Unicode text.
    """
    raise NotImplementedError()

def canonicalize(value):
    """Serialize a parsed JSON value to compact canonical UTF-8 bytes."""
    raise NotImplementedError()

def digest(canonical):
    """Return the lowercase SHA-256 hex digest of canonical bytes."""
    raise NotImplementedError()

def verify(text, expected_digest):
    """Verify a JSON document against an expected SHA-256 digest.

    Any parsing, normalization, type, or comparison error is reported as a
    failed verification instead of being allowed to escape.
    """
    raise NotImplementedError()

def canon_batch(documents, policy):
    """Canonicalize an iterable of JSON documents independently.

    Policy is either canonical or digest.  The result maps each zero-based
    document index to canonical bytes or to its lowercase SHA-256 hex digest.
    A document must never affect how another document is normalized.
    """
    raise NotImplementedError()
