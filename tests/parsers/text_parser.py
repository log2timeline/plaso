#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This file contains the tests for the generic text parser."""

import codecs
import unittest

import pyparsing

from dfvfs.file_io import fake_file_io
from dfvfs.helpers import text_file as dfvfs_text_file
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context as dfvfs_context

from plaso.lib import errors
from plaso.parsers import text_parser

from tests.parsers import test_lib


class TestPyparsingMultiLineTextParser(
    text_parser.PyparsingMultiLineTextParser):
  """Multi-line PyParsing-based text parser for testing purposes."""

  NAME = 'test'

  _ENCODING = 'utf-8'

  _LINE = pyparsing.Regex('.*') + pyparsing.lineEnd()

  LINE_STRUCTURES = [('line', _LINE)]

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    This function takes as an input a parsed pyparsing structure
    and produces an EventObject if possible from that structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.
    """
    return

  def VerifyStructure(self, parser_mediator, lines):
    """Verify the structure of the file and return boolean based on that check.

    This function should read enough text from the text file to confirm
    that the file is the correct one for this particular parser.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    return True


class PyparsingConstantsTest(test_lib.ParserTestCase):
  """Tests the PyparsingConstants text parser."""

  def testConstants(self):
    """Tests parsing with constants."""
    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.MONTH.parseString('MMo')
    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.MONTH.parseString('M')
    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.MONTH.parseString('March', parseAll=True)

    self.assertTrue(text_parser.PyparsingConstants.MONTH.parseString('Jan'))

    line = '# This is a comment.'
    parsed_line = text_parser.PyparsingConstants.COMMENT_LINE_HASH.parseString(
        line)
    self.assertEqual(parsed_line[-1], 'This is a comment.')
    self.assertEqual(len(parsed_line), 2)


class PyparsingSingleLineTextParserTest(test_lib.ParserTestCase):
  """Tests for the single-line PyParsing-based text parser."""

  # TODO: add tests for ParseFileObject


class PyparsingMultiLineTextParserTest(test_lib.ParserTestCase):
  """Tests for the multi-line PyParsing-based text parser."""

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

  # TODO: add tests for _GetValueFromStructure

  # TODO: add tests for _ParseLineStructure

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    resolver_context = dfvfs_context.Context()

    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')
    data = b'This is another file.\nWith two lines.\n'
    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, data)
    file_object.Open()

    test_parser = TestPyparsingMultiLineTextParser()
    test_parser.ParseFileObject(parser_mediator, file_object)

    # The test parser does not generate events.
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)

    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')
    data = b'This is another file.\nWith tw\xba lines.\n'
    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, data)
    file_object.Open()

    test_parser = TestPyparsingMultiLineTextParser()

    with self.assertRaises(errors.WrongParser):
      test_parser.ParseFileObject(parser_mediator, file_object)


if __name__ == '__main__':
  unittest.main()
