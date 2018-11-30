#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the CLI tools classes."""

from __future__ import unicode_literals

import argparse
import io
import locale
import os
import sys
import unittest

from plaso.cli import tools
from plaso.lib import errors

from tests.cli import test_lib


class CLIToolTest(test_lib.CLIToolTestCase):
  """Tests for the CLI tool base class."""

  # pylint: disable=protected-access

  _EXPECTED_BASIC_OPTIONS = """\
usage: tool_test.py [-h] [-V]

Test argument parser.

optional arguments:
  -V, --version  Show the version information.
  -h, --help     Show this help message and exit.
"""

  _EXPECTED_INFORMATIONAL_OPTIONS = """\
usage: tool_test.py [-d] [-q]

Test argument parser.

optional arguments:
  -d, --debug  Enable debug output.
  -q, --quiet  Disable informational output.
"""

  _EXPECTED_TIMEZONE_OPTION = """\
usage: tool_test.py [-z TIMEZONE]

Test argument parser.

optional arguments:
  -z TIMEZONE, --zone TIMEZONE, --timezone TIMEZONE
                        explicitly define the timezone. Typically the timezone
                        is determined automatically where possible otherwise
                        it will default to UTC. Use "-z list" to see a list of
                        available timezones.
"""

  # TODO: add test for _ConfigureLogging
  # TODO: add test for _EncodeString

  def testParseInformationalOptions(self):
    """Tests the _ParseInformationalOptions function."""
    test_tool = tools.CLITool()

    options = test_lib.TestOptions()
    options.debug = True
    options.quiet = True

    test_tool._ParseInformationalOptions(options)

  def testParseLogFileOptions(self):
    """Tests the _ParseLogFileOptions function."""
    test_tool = tools.CLITool()

    options = test_lib.TestOptions()
    options.log_file = 'file.log'

    test_tool._ParseLogFileOptions(options)

  def testParseTimezoneOption(self):
    """Tests the _ParseTimezoneOption function."""
    test_tool = tools.CLITool()

    options = test_lib.TestOptions()

    test_tool._ParseTimezoneOption(options)
    self.assertIsNone(test_tool._preferred_time_zone)

    options.timezone = 'list'
    test_tool._ParseTimezoneOption(options)
    self.assertIsNone(test_tool._preferred_time_zone)

    options.timezone = 'CET'
    test_tool._ParseTimezoneOption(options)
    self.assertEqual(test_tool._preferred_time_zone, 'CET')

  # TODO: add test for _PromptUserForInput

  def testAddBasicOptions(self):
    """Tests the AddBasicOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog='tool_test.py', description='Test argument parser.',
        add_help=False, formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = tools.CLITool()
    test_tool.AddBasicOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_BASIC_OPTIONS)

  def testAddInformationalOptions(self):
    """Tests the AddInformationalOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog='tool_test.py', description='Test argument parser.',
        add_help=False, formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = tools.CLITool()
    test_tool.AddInformationalOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_INFORMATIONAL_OPTIONS)

  # TODO: add test for AddLogFileOptions

  def testAddTimeZoneOption(self):
    """Tests the AddTimeZoneOption function."""
    argument_parser = argparse.ArgumentParser(
        prog='tool_test.py', description='Test argument parser.',
        add_help=False, formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = tools.CLITool()
    test_tool.AddTimeZoneOption(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_TIMEZONE_OPTION)

  def testGetCommandLineArguments(self):
    """Tests the GetCommandLineArguments function."""
    cli_tool = tools.CLITool()
    cli_tool.preferred_encoding = 'UTF-8'

    command_line_arguments = cli_tool.GetCommandLineArguments()
    self.assertIsNotNone(command_line_arguments)

  def testListTimeZones(self):
    """Tests the ListTimeZones function."""
    output_writer = test_lib.TestBinaryOutputWriter()
    cli_tool = tools.CLITool(output_writer=output_writer)

    cli_tool.ListTimeZones()

    string = output_writer.ReadOutput()
    expected_string = (
        b'\n'
        b'************************************ Zones '
        b'*************************************\n'
        b'                        Timezone : UTC Offset\n'
        b'----------------------------------------'
        b'----------------------------------------\n')
    self.assertTrue(string.startswith(expected_string))

  def testParseNumericOption(self):
    """Tests the ParseNumericOption function."""
    output_writer = test_lib.TestBinaryOutputWriter()
    cli_tool = tools.CLITool(output_writer=output_writer)

    options = test_lib.TestOptions()

    numeric_value = cli_tool.ParseNumericOption(options, 'buffer_size')
    self.assertIsNone(numeric_value)

    numeric_value = cli_tool.ParseNumericOption(
        options, 'buffer_size', default_value=0)
    self.assertEqual(numeric_value, 0)

    options.buffer_size = '10'

    numeric_value = cli_tool.ParseNumericOption(options, 'buffer_size')
    self.assertEqual(numeric_value, 10)

    numeric_value = cli_tool.ParseNumericOption(
        options, 'buffer_size', base=16)
    self.assertEqual(numeric_value, 16)

    options.buffer_size = 'bogus'

    with self.assertRaises(errors.BadConfigOption):
      cli_tool.ParseNumericOption(options, 'buffer_size')

    options.buffer_size = (1, 'bogus')

    with self.assertRaises(errors.BadConfigOption):
      cli_tool.ParseNumericOption(options, 'buffer_size')

  def testParseStringOption(self):
    """Tests the ParseStringOption function."""
    encoding = sys.stdin.encoding

    # Note that sys.stdin.encoding can be None.
    if not encoding:
      encoding = locale.getpreferredencoding()

    cli_tool = tools.CLITool()
    cli_tool.preferred_encoding = 'UTF-8'

    expected_string = 'Test Unicode string'
    options = test_lib.TestOptions()
    options.test = expected_string

    string = cli_tool.ParseStringOption(options, 'test')
    self.assertEqual(string, expected_string)

    options = test_lib.TestOptions()

    string = cli_tool.ParseStringOption(options, 'test')
    self.assertIsNone(string)

    string = cli_tool.ParseStringOption(
        options, 'test', default_value=expected_string)
    self.assertEqual(string, expected_string)

    options = test_lib.TestOptions()
    options.test = expected_string.encode(encoding)

    string = cli_tool.ParseStringOption(options, 'test')
    self.assertEqual(string, expected_string)

    if encoding and encoding.upper() == 'UTF-8':
      options = test_lib.TestOptions()
      options.test = (
          b'\xad\xfd\xab\x73\x99\xc7\xb4\x78\xd0\x8c\x8a\xee\x6d\x6a\xcb\x90')

      with self.assertRaises(errors.BadConfigOption):
        cli_tool.ParseStringOption(options, 'test')

  def testPrintSeparatorLine(self):
    """Tests the PrintSeparatorLine function."""
    output_writer = test_lib.TestBinaryOutputWriter()
    cli_tool = tools.CLITool(output_writer=output_writer)

    cli_tool.PrintSeparatorLine()
    string = output_writer.ReadOutput()
    expected_string = (
        b'----------------------------------------'
        b'----------------------------------------\n')
    self.assertEqual(string, expected_string)


class CLIInputReaderTest(test_lib.CLIToolTestCase):
  """Tests for the command line interface input reader interface."""

  def testInitialize(self):
    """Tests the __init__ function."""
    input_reader = tools.CLIInputReader()
    self.assertIsNotNone(input_reader)


class FileObjectInputReaderTest(unittest.TestCase):
  """Tests for the file object command line interface input reader."""

  def testInitialize(self):
    """Tests the __init__ function."""
    input_reader = tools.StdinInputReader()
    self.assertIsNotNone(input_reader)

  _TEST_DATA = (
      b'A first string\n'
      b'A 2nd string\n'
      b'\xc3\xberi\xc3\xb0ja string\n'
      b'\xff\xfef\x00j\x00\xf3\x00r\x00\xf0\x00a\x00 \x00b\x00a\x00n\x00d\x00')

  def testReadAscii(self):
    """Tests the Read function with ASCII encoding."""
    file_object = io.BytesIO(self._TEST_DATA)
    input_reader = tools.FileObjectInputReader(file_object, encoding='ascii')

    string = input_reader.Read()
    self.assertEqual(string, 'A first string\n')

    string = input_reader.Read()
    self.assertEqual(string, 'A 2nd string\n')

    # UTF-8 string with non-ASCII characters.
    string = input_reader.Read()
    self.assertEqual(string, '\ufffd\ufffdri\ufffd\ufffdja string\n')

    # UTF-16 string with non-ASCII characters.
    string = input_reader.Read()
    expected_string = (
        '\ufffd\ufffdf\x00j\x00\ufffd\x00r\x00\ufffd\x00a\x00 '
        '\x00b\x00a\x00n\x00d\x00')
    self.assertEqual(string, expected_string)

  def testReadUtf8(self):
    """Tests the Read function with UTF-8 encoding."""
    file_object = io.BytesIO(self._TEST_DATA)
    input_reader = tools.FileObjectInputReader(file_object)

    string = input_reader.Read()
    self.assertEqual(string, 'A first string\n')

    string = input_reader.Read()
    self.assertEqual(string, 'A 2nd string\n')

    # UTF-8 string with non-ASCII characters.
    string = input_reader.Read()
    self.assertEqual(string, 'þriðja string\n')

    # UTF-16 string with non-ASCII characters.
    string = input_reader.Read()
    expected_string = (
        '\ufffd\ufffdf\x00j\x00\ufffd\x00r\x00\ufffd\x00a\x00 '
        '\x00b\x00a\x00n\x00d\x00')
    self.assertEqual(string, expected_string)


class StdinInputReaderTest(unittest.TestCase):
  """Tests for the stdin command line interface input reader."""

  def testInitialize(self):
    """Tests the __init__ function."""
    input_reader = tools.StdinInputReader()
    self.assertIsNotNone(input_reader)


class FileObjectOutputWriterTest(unittest.TestCase):
  """Tests for the file object command line interface output writer."""

  def _ReadOutput(self, file_object):
    """Reads all output added since the last call to ReadOutput.

    Args:
      file_object (file): file-like object.

    Returns:
      str: output data.
    """
    file_object.seek(0, os.SEEK_SET)
    output_data = file_object.read()

    file_object.seek(0, os.SEEK_SET)
    file_object.truncate(0)
    return output_data

  def testWriteAscii(self):
    """Tests the Write function with ASCII encoding."""
    file_object = io.BytesIO()
    output_writer = tools.FileObjectOutputWriter(
        file_object, encoding='ascii')

    output_writer.Write('A first string\n')

    byte_stream = self._ReadOutput(file_object)
    self.assertEqual(byte_stream, b'A first string\n')

    # Unicode string with non-ASCII characters.
    output_writer.Write('þriðja string\n')

    byte_stream = self._ReadOutput(file_object)
    self.assertEqual(byte_stream, b'?ri?ja string\n')

  def testWriteUtf8(self):
    """Tests the Write function with UTF-8 encoding."""
    file_object = io.BytesIO()
    output_writer = tools.FileObjectOutputWriter(file_object)

    output_writer.Write('A first string\n')

    byte_stream = self._ReadOutput(file_object)
    self.assertEqual(byte_stream, b'A first string\n')

    # Unicode string with non-ASCII characters.
    output_writer.Write('þriðja string\n')

    byte_stream = self._ReadOutput(file_object)
    self.assertEqual(byte_stream, b'\xc3\xberi\xc3\xb0ja string\n')


class StdoutOutputWriterTest(unittest.TestCase):
  """Tests for the stdout command line interface output writer."""

  def testWriteAscii(self):
    """Tests the Write function with ASCII encoding."""
    output_writer = tools.StdoutOutputWriter(encoding='ascii')
    output_writer.Write('A first string\n')


if __name__ == '__main__':
  unittest.main()
