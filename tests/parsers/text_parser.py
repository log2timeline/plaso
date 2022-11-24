#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This file contains the tests for the generic text parser."""

import unittest

from dfvfs.file_io import fake_file_io
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context as dfvfs_context

from plaso.parsers import text_parser

from tests.parsers import test_lib


class EncodedTextReaderTest(test_lib.ParserTestCase):
  """Tests for encoded text reader."""

  _TEST_LINES ='\n'.join([
      'Multiple lines',
      'of text',
      'in a single',
      'file.'])

  _TEST_DATA = _TEST_LINES.encode('utf-8')

  def _EncodingErrorHandler(self, exception):
    """Encoding error handler.

    Args:
      exception [UnicodeDecodeError]: exception.

    Returns:
      tuple[str, int]: replacement string and number of bytes to skip.

    Raises:
      TypeError: if exception is not of type UnicodeDecodeError.
    """
    if not isinstance(exception, UnicodeDecodeError):
      raise TypeError('Unsupported exception type.')

    # pylint: disable=attribute-defined-outside-init,no-member
    self._encoding_errors.append(
        (exception.start, exception.object[exception.start]))
    escaped = '\\x{0:2x}'.format(exception.object[exception.start])
    return (escaped, exception.start + 1)

  def testReadLine(self):
    """Tests the ReadLine function."""
    resolver_context = dfvfs_context.Context()

    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')
    file_object = fake_file_io.FakeFile(
        resolver_context, test_path_spec, self._TEST_DATA)
    file_object.Open()

    text_reader = text_parser.EncodedTextReader(file_object)

    line = text_reader.ReadLine()
    self.assertEqual(line, 'Multiple lines')

    line = text_reader.ReadLine()
    self.assertEqual(line, 'of text')

  def testReadLines(self):
    """Tests the ReadLines function."""
    resolver_context = dfvfs_context.Context()

    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')
    file_object = fake_file_io.FakeFile(
        resolver_context, test_path_spec, self._TEST_DATA)
    file_object.Open()

    text_reader = text_parser.EncodedTextReader(file_object)

    text_reader.ReadLines()
    self.assertEqual(text_reader.lines, self._TEST_LINES)

  def testSkipAhead(self):
    """Tests the SkipAhead function."""
    resolver_context = dfvfs_context.Context()

    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')
    file_object = fake_file_io.FakeFile(
        resolver_context, test_path_spec, self._TEST_DATA)
    file_object.Open()

    text_reader = text_parser.EncodedTextReader(file_object)

    text_reader.SkipAhead(10)
    self.assertEqual(text_reader.lines, self._TEST_LINES[10:])


class SingleLineTextParserTest(test_lib.ParserTestCase):
  """Tests for the single-line text parser."""

  # TODO: add tests for ParseFileObject


if __name__ == '__main__':
  unittest.main()
