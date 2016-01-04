# -*- coding: utf-8 -*-
"""The Python 2 and 3 compatible type definitions."""

import sys


if sys.version_info[0] < 3:
  BYTES_TYPE = str
  INTEGER_TYPES = (int, long)
  LONG_TYPE = long
  STRING_TYPES = (basestring)
  UNICODE_TYPE = unicode
else:
  BYTES_TYPE = bytes
  INTEGER_TYPES = (int)
  LONG_TYPE = int
  STRING_TYPES = (str)
  UNICODE_TYPE = str
