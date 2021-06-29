#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for delimiter separated values shared output module."""

import unittest

from tests.output import test_lib


class DSVOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests the delimiter separated values shared output module."""

  # TODO: add coverage for _SanitizeField
  # TODO: add coverage for SetFieldDelimiter
  # TODO: add coverage for SetFields


if __name__ == '__main__':
  unittest.main()
