# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import decimal
import fractions
import itertools
import re
import sys
import uuid

import pyrfc3339

from .immutable_dict import ImmutableDict
from .immutable_list import ImmutableList
from .edn_lex import Keyword, Symbol
from .edn_parse import TaggedElement


# alias Python 2 types to their corresponding types in Python 3 if necessary
if sys.version_info[0] >= 3:
    __PY3 = True
    long = int
    basestring = str
    unicode = str
    unichr = chr
else:
    __PY3 = False


DEFAULT_INPUT_ENCODING = 'utf-8'
DEFAULT_OUTPUT_ENCODING = 'utf-8'

# proper unicode escaping
# see http://stackoverflow.com/a/24519338
ESCAPE = re.compile(r'[\x00-\x1f\\"\b\f\n\r\t]', re.UNICODE)
ESCAPE_DCT = {
    '\\': '\\\\',
    '"': '\\"',
    '\b': '\\b',
    '\f': '\\f',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
}

for __i in range(0x20):
    ESCAPE_DCT.setdefault(unichr(__i), '\\u{0:04x}'.format(__i))
del __i


def unicode_escape(string):
    """Return a edn representation of a Python string"""
    def replace(match):
        return ESCAPE_DCT[match.group(0)]
    return '"' + ESCAPE.sub(replace, string) + '"'

class Dumper(object):
    def __init__(self,
            string_encoding=DEFAULT_INPUT_ENCODING,
            output_encoding=None,
            keyword_keys=False,
            sort_keys=False,
            sort_sets=False,
            pretty=False):

        self.string_encoding = string_encoding
        self.output_encoding = output_encoding
        self.keyword_keys = keyword_keys
        self.sort_keys = sort_keys
        self.sort_sets = sort_sets
        self.pretty = pretty
        self._indent = 

    def _dump_seq(self, objs):
        return ' '.join([self._dump(obj) for obj in objs])

    def _dump(self, obj):
        if obj is None:
            return 'nil'
        if isinstance(obj, bool):
            return 'true' if obj else 'false'
        if isinstance(obj, (int, long, float)):
            return unicode(obj)
        if isinstance(obj, decimal.Decimal):
            return '{}M'.format(obj)
        if isinstance(obj, (Keyword, Symbol)):
            return unicode(obj)
        # CAVEAT LECTOR! In Python 3 'basestring' is alised to 'str' above.
        # Furthermore, in Python 2 bytes is an instance of 'str'/'basestring' while
        # in Python 3 it is not.
        if isinstance(obj, bytes):
            return unicode_escape(obj.decode(self.string_encoding))
        if isinstance(obj, basestring):
            return unicode_escape(obj)
        if isinstance(obj, tuple):
            return '({})'.format(self._dump_seq(obj))
        if isinstance(obj, (list, ImmutableList)):
            return '[{}]'.format(self._dump_seq(obj))
        if isinstance(obj, set) or isinstance(obj, frozenset):
            if self.sort_sets:
                obj = sorted(obj)
            return '#{{{}}}'.format(self._dump_seq(obj))
        if isinstance(obj, dict) or isinstance(obj, ImmutableDict):
            pairs = obj.items()
            if self.sort_keys:
                pairs = sorted(pairs, key=lambda p: str(p[0]))
            if self.keyword_keys:
                pairs = ((Keyword(k) if isinstance(k, (bytes, basestring)) else k, v) for k, v in pairs)

            return '{{{}}}'.format(self._dump_seq(itertools.chain.from_iterable(pairs)))
        if isinstance(obj, fractions.Fraction):
            return '{}/{}'.format(obj.numerator, obj.denominator)
        if isinstance(obj, datetime.datetime):
            return '#inst "{}"'.format(pyrfc3339.generate(obj, microseconds=True))
        if isinstance(obj, datetime.date):
            return '#inst "{}"'.format(obj.isoformat())
        if isinstance(obj, uuid.UUID):
            return '#uuid "{}"'.format(obj)
        if isinstance(obj, TaggedElement):
            return unicode(obj)
        raise NotImplementedError(
            u"encountered object of type '{}' for which no known encoding is available: {}".format(
                type(obj), repr(obj)))

    def dump(self, obj):
        s = self._dump(obj)
        if self.output_encoding:
            s = s.encode(self.output_encoding)
        return s

def dump(obj,
         string_encoding=DEFAULT_INPUT_ENCODING,
         output_encoding=DEFAULT_OUTPUT_ENCODING,
         keyword_keys=False,
         sort_keys=False,
         sort_sets=False,
         pretty=False):
    dumper = Dumper(output_encoding=None if __PY3 else output_encoding,
                    string_encoding=string_encoding,
                    keyword_keys=keyword_keys,
                    sort_keys=sort_keys,
                    sort_sets=sort_sets,
                    pretty=pretty)

    return dumper.dump(obj)
