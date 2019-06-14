#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the CLI argument helper interface."""

from __future__ import unicode_literals

import locale
import sys
import unittest

from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class HelperManagerTest(unittest.TestCase):
  """Tests the parsers manager."""

  # pylint: disable=protected-access

  def testParseNumericOption(self):
    """Tests the _ParseNumericOption function."""
    test_helper = test_lib.TestHelper()

    expected_integer = 123
    options = cli_test_lib.TestOptions()
    options.test = expected_integer

    integer = test_helper._ParseNumericOption(options, 'test')
    self.assertEqual(integer, expected_integer)

    options = cli_test_lib.TestOptions()

    integer = test_helper._ParseNumericOption(options, 'test')
    self.assertIsNone(integer)

    integer = test_helper._ParseNumericOption(
        options, 'test', default_value=expected_integer)
    self.assertEqual(integer, expected_integer)

    options = cli_test_lib.TestOptions()
    options.test = b'abc'

    with self.assertRaises(errors.BadConfigOption):
      test_helper._ParseNumericOption(options, 'test')

  def testParseStringOption(self):
    """Tests the _ParseStringOption function."""
    encoding = sys.stdin.encoding

    # Note that sys.stdin.encoding can be None.
    if not encoding:
      encoding = locale.getpreferredencoding()

    test_helper = test_lib.TestHelper()

    expected_string = 'Test Unicode string'
    options = cli_test_lib.TestOptions()
    options.test = expected_string

    string = test_helper._ParseStringOption(options, 'test')
    self.assertEqual(string, expected_string)

    options = cli_test_lib.TestOptions()

    string = test_helper._ParseStringOption(options, 'test')
    self.assertIsNone(string)

    string = test_helper._ParseStringOption(
        options, 'test', default_value=expected_string)
    self.assertEqual(string, expected_string)

    options = cli_test_lib.TestOptions()
    options.test = expected_string.encode(encoding)

    string = test_helper._ParseStringOption(options, 'test')
    self.assertEqual(string, expected_string)

    if encoding and encoding == 'UTF-8':
      options = cli_test_lib.TestOptions()
      options.test = (
          b'\xad\xfd\xab\x73\x99\xc7\xb4\x78\xd0\x8c\x8a\xee\x6d\x6a\xcb\x90')

      with self.assertRaises(errors.BadConfigOption):
        test_helper._ParseStringOption(options, 'test')


if __name__ == '__main__':
  unittest.main()
