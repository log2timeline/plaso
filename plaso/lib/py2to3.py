# -*- coding: utf-8 -*-
"""The Python 2 and 3 compatible type definitions."""

import sys


# pylint: disable=invalid-name,undefined-variable

if sys.version_info[0] < 3:
  BYTES_TYPE = str
  INTEGER_TYPES = (int, long)
  LONG_TYPE = long
  STRING_TYPES = (basestring, )
  UNICHR = unichr
  UNICODE_TYPE = unicode
else:
  BYTES_TYPE = bytes
  INTEGER_TYPES = (int, )
  LONG_TYPE = int
  STRING_TYPES = (str, )
  UNICHR = chr
  UNICODE_TYPE = str
