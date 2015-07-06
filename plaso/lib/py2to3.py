# -*- coding: utf-8 -*-
"""The Python 2 and 3 compatible type definitions."""

import sys


if sys.version_info[0] < 3:
  BYTES_TYPE = str
  UNICODE_TYPE = unicode
else:
  BYTES_TYPE = bytes
  UNICODE_TYPE = str
