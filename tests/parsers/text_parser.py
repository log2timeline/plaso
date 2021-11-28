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

from plaso.parsers import text_parser

from tests.parsers import test_lib


class TestPyparsingSingleLineTextParser(
    text_parser.PyparsingSingleLineTextParser):
  """Single line PyParsing-based text parser for testing purposes."""

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

  def VerifyStructure(self, parser_mediator, line):
    """Verify the structure of the file and return boolean based on that check.

    This function should read enough text from the text file to confirm
    that the file is the correct one for this particular parser.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (str): single line from the text file.

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

  def testConstantIPv4(self):
    """Tests parsing with the IPV4_ADDRESS constant."""
    self.assertTrue(
        text_parser.PyparsingConstants.IPV4_ADDRESS.parseString(
            '123.51.234.52'))
    self.assertTrue(
        text_parser.PyparsingConstants.IPV4_ADDRESS.parseString(
            '255.254.23.1'))
    self.assertTrue(
        text_parser.PyparsingConstants.IPV4_ADDRESS.parseString('1.1.34.2'))

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_ADDRESS.parseString('a.1.34.258')

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_ADDRESS.parseString('.34.258')

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_ADDRESS.parseString('34.258')


class PyparsingSingleLineTextParserTest(test_lib.ParserTestCase):
  """Tests for the single line PyParsing-based text parser."""

  # pylint: disable=attribute-defined-outside-init,protected-access

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

    self._encoding_errors.append(
        (exception.start, exception.object[exception.start]))
    escaped = '\\x{0:2x}'.format(exception.object[exception.start])
    return (escaped, exception.start + 1)

  def testIsText(self):
    """Tests the _IsText function."""
    test_parser = TestPyparsingSingleLineTextParser()

    bytes_in = b'this is My Weird ASCII and non whatever string.'
    self.assertTrue(test_parser._IsText(bytes_in))

    bytes_in = 'Plaso Síar Og Raðar Þessu'
    self.assertTrue(test_parser._IsText(bytes_in))

    bytes_in = b'\x01\\62LSO\xFF'
    self.assertFalse(test_parser._IsText(bytes_in))

    bytes_in = b'T\x00h\x00i\x00s\x00\x20\x00'
    self.assertTrue(test_parser._IsText(bytes_in))

    bytes_in = b'Ascii\x00'
    self.assertTrue(test_parser._IsText(bytes_in))

    bytes_in = b'Ascii Open then...\x00\x99\x23'
    self.assertFalse(test_parser._IsText(bytes_in))

  def testReadLine(self):
    """Tests the _ReadLine function."""
    resolver_context = dfvfs_context.Context()

    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')
    data = b'This is another file.'
    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, data)
    file_object.Open()

    test_parser = TestPyparsingSingleLineTextParser()
    test_text_file = dfvfs_text_file.TextFile(file_object, encoding='utf-8')
    line = test_parser._ReadLine(test_text_file)
    self.assertEqual(line, 'This is another file.')

    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')
    data = b'This is an\xbather file.'
    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, data)
    file_object.Open()

    test_parser = TestPyparsingSingleLineTextParser()
    test_text_file = dfvfs_text_file.TextFile(file_object, encoding='utf8')
    with self.assertRaises(UnicodeDecodeError):
      test_parser._ReadLine(test_text_file)

    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')
    data = b'This is an\xbather file.'
    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, data)
    file_object.Open()

    test_parser = TestPyparsingSingleLineTextParser()
    test_text_file = dfvfs_text_file.TextFile(
        file_object, encoding='utf8', encoding_errors='replace')
    line = test_parser._ReadLine(test_text_file)
    self.assertEqual(line, 'This is an\ufffdther file.')

    self._encoding_errors = []
    codecs.register_error('test_handler', self._EncodingErrorHandler)

    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')
    data = b'This is an\xbather file.'
    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, data)
    file_object.Open()

    test_parser = TestPyparsingSingleLineTextParser()
    test_text_file = dfvfs_text_file.TextFile(
        file_object, encoding='utf8', encoding_errors='test_handler')
    line = test_parser._ReadLine(test_text_file)
    self.assertEqual(line, 'This is an\\xbather file.')

    self.assertEqual(len(self._encoding_errors), 1)
    self.assertEqual(self._encoding_errors[0], (10, 0xba))

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    resolver_context = dfvfs_context.Context()

    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')
    data = b'This is another file.\nWith two lines.\n'
    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, data)
    file_object.Open()

    test_parser = TestPyparsingSingleLineTextParser()
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

    test_parser = TestPyparsingSingleLineTextParser()
    test_parser.ParseFileObject(parser_mediator, file_object)

    # The test parser does not generate events.
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)


if __name__ == '__main__':
  unittest.main()
