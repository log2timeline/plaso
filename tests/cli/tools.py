#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the CLI tools classes."""

import argparse
import io
import sys
import unittest

from plaso.cli import tools
from plaso.lib import errors

from tests.cli import test_lib


class CLIToolTest(test_lib.CLIToolTestCase):
  """Tests for the CLI tool base class."""

  _EXPECTED_BASIC_OPTIONS = u'\n'.join([
      u'usage: tool_test.py [-h] [-V]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  -h, --help     show this help message and exit.',
      u'  -V, --version  show the version information.',
      u''])

  _EXPECTED_DATA_OPTION = u'\n'.join([
      u'usage: tool_test.py [--data PATH]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --data PATH  the location of the data files.',
      u''])

  _EXPECTED_INFORMATIONAL_OPTIONS = u'\n'.join([
      u'usage: tool_test.py [-d] [-q]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  -d, --debug  enable debug output.',
      u'  -q, --quiet  disable informational output.',
      u''])

  _EXPECTED_TIMEZONE_OPTION = u'\n'.join([
      u'usage: tool_test.py [-z TIMEZONE]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  -z TIMEZONE, --zone TIMEZONE, --timezone TIMEZONE',
      (u'                        explicitly define the timezone. Typically '
       u'the timezone'),
      (u'                        is determined automatically where possible. '
       u'Use "-z'),
      u'                        list" to see a list of available timezones.',
      u''])

  def testAddBasicOptions(self):
    """Tests the AddBasicOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'tool_test.py', description=u'Test argument parser.',
        add_help=False, formatter_class=argparse.RawDescriptionHelpFormatter)

    test_tool = tools.CLITool()
    test_tool.AddBasicOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_BASIC_OPTIONS)

  def testAddDataLocationOption(self):
    """Tests the AddDataLocationOption function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'tool_test.py', description=u'Test argument parser.',
        add_help=False, formatter_class=argparse.RawDescriptionHelpFormatter)

    test_tool = tools.CLITool()
    test_tool.AddDataLocationOption(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_DATA_OPTION)

  def testAddInformationalOptions(self):
    """Tests the AddInformationalOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'tool_test.py', description=u'Test argument parser.',
        add_help=False, formatter_class=argparse.RawDescriptionHelpFormatter)

    test_tool = tools.CLITool()
    test_tool.AddInformationalOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_INFORMATIONAL_OPTIONS)

  def testAddTimezoneOption(self):
    """Tests the AddTimezoneOption function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'tool_test.py', description=u'Test argument parser.',
        add_help=False, formatter_class=argparse.RawDescriptionHelpFormatter)

    test_tool = tools.CLITool()
    test_tool.AddTimezoneOption(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_TIMEZONE_OPTION)

  def testGetCommandLineArguments(self):
    """Tests the GetCommandLineArguments function."""
    cli_tool = tools.CLITool()
    cli_tool.preferred_encoding = u'UTF-8'

    command_line_arguments = cli_tool.GetCommandLineArguments()
    self.assertIsNotNone(command_line_arguments)

  def testListTimeZones(self):
    """Tests the ListTimeZones function."""
    output_writer = test_lib.TestOutputWriter()
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

  def testParseStringOption(self):
    """Tests the ParseStringOption function."""
    encoding = sys.stdin.encoding

    # Note that sys.stdin.encoding can be None.
    if not encoding:
      encoding = self.preferred_encoding

    cli_tool = tools.CLITool()
    cli_tool.preferred_encoding = u'UTF-8'

    expected_string = u'Test Unicode string'
    options = test_lib.TestOptions()
    options.test = expected_string

    string = cli_tool.ParseStringOption(options, u'test')
    self.assertEqual(string, expected_string)

    options = test_lib.TestOptions()

    string = cli_tool.ParseStringOption(options, u'test')
    self.assertIsNone(string)

    string = cli_tool.ParseStringOption(
        options, u'test', default_value=expected_string)
    self.assertEqual(string, expected_string)

    options = test_lib.TestOptions()
    options.test = expected_string.encode(encoding)

    string = cli_tool.ParseStringOption(options, u'test')
    self.assertEqual(string, expected_string)

    if not sys.stdin.encoding and sys.stdin.encoding.upper() == u'UTF-8':
      options = test_lib.TestOptions()
      options.test = (
          b'\xad\xfd\xab\x73\x99\xc7\xb4\x78\xd0\x8c\x8a\xee\x6d\x6a\xcb\x90')

      with self.assertRaises(errors.BadConfigOption):
        cli_tool.ParseStringOption(options, u'test')

  def testPrintSeparatorLine(self):
    """Tests the PrintSeparatorLine function."""
    output_writer = test_lib.TestOutputWriter()
    cli_tool = tools.CLITool(output_writer=output_writer)

    cli_tool.PrintSeparatorLine()
    string = output_writer.ReadOutput()
    expected_string = (
        b'----------------------------------------'
        b'----------------------------------------\n')
    self.assertEqual(string, expected_string)


class StdinInputReaderTest(unittest.TestCase):
  """The unit test case for a stdin input reader."""

  _TEST_DATA = (
      b'A first string\n'
      b'A 2nd string\n'
      b'\xc3\xberi\xc3\xb0ja string\n'
      b'\xff\xfef\x00j\x00\xf3\x00r\x00\xf0\x00a\x00 \x00b\x00a\x00n\x00d\x00')

  def testReadAscii(self):
    """Tests the Read function with ASCII encoding."""
    original_stdin = sys.stdin
    sys.stdin = io.BytesIO(self._TEST_DATA)

    input_reader = tools.StdinInputReader(encoding=u'ascii')

    string = input_reader.Read()
    self.assertEqual(string, u'A first string\n')

    string = input_reader.Read()
    self.assertEqual(string, u'A 2nd string\n')

    # UTF-8 string with non-ASCII characters.
    string = input_reader.Read()
    self.assertEqual(string, u'\ufffd\ufffdri\ufffd\ufffdja string\n')

    # UTF-16 string with non-ASCII characters.
    string = input_reader.Read()
    expected_string = (
        u'\ufffd\ufffdf\x00j\x00\ufffd\x00r\x00\ufffd\x00a\x00 '
        u'\x00b\x00a\x00n\x00d\x00')
    self.assertEqual(string, expected_string)

    sys.stdin = original_stdin

  def testReadUtf8(self):
    """Tests the Read function with UTF-8 encoding."""
    original_stdin = sys.stdin
    sys.stdin = io.BytesIO(self._TEST_DATA)

    input_reader = tools.StdinInputReader()

    string = input_reader.Read()
    self.assertEqual(string, u'A first string\n')

    string = input_reader.Read()
    self.assertEqual(string, u'A 2nd string\n')

    # UTF-8 string with non-ASCII characters.
    string = input_reader.Read()
    self.assertEqual(string, u'þriðja string\n')

    # UTF-16 string with non-ASCII characters.
    string = input_reader.Read()
    expected_string = (
        u'\ufffd\ufffdf\x00j\x00\ufffd\x00r\x00\ufffd\x00a\x00 '
        u'\x00b\x00a\x00n\x00d\x00')
    self.assertEqual(string, expected_string)

    sys.stdin = original_stdin


class FileObjectOutputWriterTest(unittest.TestCase):
  """The unit test case for a file-like object output writer."""

  def testWriteAscii(self):
    """Tests the Write function with ASCII encoding."""
    output_writer = test_lib.TestOutputWriter(encoding=u'ascii')

    output_writer.Write(u'A first string\n')
    string = output_writer.ReadOutput()
    self.assertEqual(string, b'A first string\n')

    # Byte string with ASCII characters.
    output_writer.Write(b'A 2nd string\n')
    string = output_writer.ReadOutput()
    self.assertEqual(string, b'A 2nd string\n')

    # Unicode string with non-ASCII characters.
    output_writer.Write(u'þriðja string\n')
    string = output_writer.ReadOutput()
    self.assertEqual(string, b'?ri?ja string\n')

    # Byte string with non-ASCII characters.
    with self.assertRaises(UnicodeDecodeError):
      # This fails because the byte string cannot be converted to
      # a Unicode string before the call to encode().
      output_writer.Write(b'\xc3\xberi\xc3\xb0ja string\n')

  def testWriteUtf8(self):
    """Tests the Write function with UTF-8 encoding."""
    output_writer = test_lib.TestOutputWriter()

    output_writer.Write(u'A first string\n')
    string = output_writer.ReadOutput()
    self.assertEqual(string, b'A first string\n')

    # Byte string with ASCII characters.
    output_writer.Write(b'A 2nd string\n')
    string = output_writer.ReadOutput()
    self.assertEqual(string, b'A 2nd string\n')

    # Unicode string with non-ASCII characters.
    output_writer.Write(u'þriðja string\n')
    string = output_writer.ReadOutput()
    self.assertEqual(string, b'\xc3\xberi\xc3\xb0ja string\n')

    # Byte string with non-ASCII characters.
    with self.assertRaises(UnicodeDecodeError):
      # This fails because the byte string cannot be converted to
      # a Unicode string before the call to encode().
      output_writer.Write(b'\xc3\xberi\xc3\xb0ja string\n')


if __name__ == '__main__':
  unittest.main()
