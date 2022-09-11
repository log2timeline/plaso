#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the text plugins interface."""

import codecs
import unittest

from dfvfs.file_io import fake_file_io
from dfvfs.helpers import text_file as dfvfs_text_file
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context as dfvfs_context

from plaso.parsers.text_plugins import interface

from tests.parsers import test_lib


class TextPluginTest(test_lib.ParserTestCase):
  """Tests for the text plugins interface."""

  # pylint: disable=protected-access

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

    # pylint: disable=attribute-defined-outside-init
    self._encoding_errors.append(
        (exception.start, exception.object[exception.start]))
    escaped = '\\x{0:2x}'.format(exception.object[exception.start])
    return (escaped, exception.start + 1)

  # TODO: add tests for _GetMatchingLineStructure
  # TODO: add tests for _GetValueFromStructure
  # TODO: add tests for _ParseLines
  # TODO: add tests for _ParseLineStructure

  def testReadLineOfText(self):
    """Tests the _ReadLineOfText function."""
    resolver_context = dfvfs_context.Context()

    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')
    data = b'This is another file.'
    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, data)
    file_object.Open()

    test_plugin = interface.TextPlugin()
    test_text_file = dfvfs_text_file.TextFile(file_object, encoding='utf-8')
    line = test_plugin._ReadLineOfText(test_text_file)
    self.assertEqual(line, 'This is another file.')

    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')
    data = b'This is an\xbather file.'
    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, data)
    file_object.Open()

    test_plugin = interface.TextPlugin()
    test_text_file = dfvfs_text_file.TextFile(file_object, encoding='utf8')
    with self.assertRaises(UnicodeDecodeError):
      test_plugin._ReadLineOfText(test_text_file)

    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')
    data = b'This is an\xbather file.'
    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, data)
    file_object.Open()

    test_plugin = interface.TextPlugin()
    test_text_file = dfvfs_text_file.TextFile(
        file_object, encoding='utf8', encoding_errors='replace')
    line = test_plugin._ReadLineOfText(test_text_file)
    self.assertEqual(line, 'This is an\ufffdther file.')

    # pylint: disable=attribute-defined-outside-init
    self._encoding_errors = []
    codecs.register_error('test_handler', self._EncodingErrorHandler)

    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')
    data = b'This is an\xbather file.'
    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, data)
    file_object.Open()

    test_plugin = interface.TextPlugin()
    test_text_file = dfvfs_text_file.TextFile(
        file_object, encoding='utf8', encoding_errors='test_handler')
    line = test_plugin._ReadLineOfText(test_text_file)
    self.assertEqual(line, 'This is an\\xbather file.')

    self.assertEqual(len(self._encoding_errors), 1)
    self.assertEqual(self._encoding_errors[0], (10, 0xba))

    # TODO: add tests for _SetLineStructures
    # TODO: add tests for Process


if __name__ == '__main__':
  unittest.main()
