# -*- coding: utf-8 -*-
"""The Python 2 and 3 compatible type definitions."""

import sys


if sys.version_info[0] < 3:
  BYTES_TYPE = str
  INTEGER_TYPES = (int, long)
  UNICODE_TYPE = unicode
else:
  BYTES_TYPE = bytes
  INTEGER_TYPES = (int)
  UNICODE_TYPE = str
