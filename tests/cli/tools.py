#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the CLI tools classes."""

from __future__ import unicode_literals

import argparse
import io
import locale
import sys
import unittest

from plaso.cli import tools
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class CLIToolTest(test_lib.CLIToolTestCase):
  """Tests for the CLI tool base class."""

  # pylint: disable=protected-access

  _EXPECTED_BASIC_OPTIONS = '\n'.join([
      'usage: tool_test.py [-h] [-V]',
      '',
      'Test argument parser.',
      '',
      'optional arguments:',
      '  -V, --version  show the version information.',
      '  -h, --help     show this help message and exit.',
      ''])

  _EXPECTED_INFORMATIONAL_OPTIONS = '\n'.join([
      'usage: tool_test.py [-d] [-q]',
      '',
      'Test argument parser.',
      '',
      'optional arguments:',
      '  -d, --debug  enable debug output.',
      '  -q, --quiet  disable informational output.',
      ''])

  _EXPECTED_PROFILING_OPTIONS = '\n'.join([
      'usage: tool_test.py [--profilers PROFILERS_LIST]',
      '                    [--profiling_directory DIRECTORY]',
      '                    [--profiling_sample_rate SAMPLE_RATE]',
      '',
      'Test argument parser.',
      '',
      'optional arguments:',
      '  --profilers PROFILERS_LIST',
      ('                        Define a list of profilers to use by the '
       'tool. This is'),
      ('                        a comma separated list where each entry is '
       'the name of'),
      ('                        a profiler. Use "--profilers list" to list '
       'the'),
      '                        available profilers.',
      '  --profiling_directory DIRECTORY, --profiling-directory DIRECTORY',
      ('                        Path to the directory that should be used '
       'to store the'),
      ('                        profiling sample files. By default the '
       'sample files'),
      '                        are stored in the current working directory.',
      ('  --profiling_sample_rate SAMPLE_RATE, '
       '--profiling-sample-rate SAMPLE_RATE'),
      ('                        The profiling sample rate (defaults to a '
       'sample every'),
      '                        1000 files).',
      ''])

  _EXPECTED_TIMEZONE_OPTION = '\n'.join([
      'usage: tool_test.py [-z TIMEZONE]',
      '',
      'Test argument parser.',
      '',
      'optional arguments:',
      '  -z TIMEZONE, --zone TIMEZONE, --timezone TIMEZONE',
      ('                        explicitly define the timezone. Typically '
       'the timezone'),
      ('                        is determined automatically where possible '
       'otherwise'),
      ('                        it will default to UTC. Use "-z list" to see '
       'a list of'),
      '                        available timezones.',
      ''])

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

  def testParseProfilingOptions(self):
    """Tests the _ParseProfilingOptions function."""
    test_tool = tools.CLITool()

    options = test_lib.TestOptions()
    options.profiling_sample_rate = '100'

    test_tool._ParseProfilingOptions(options)
    self.assertEqual(test_tool._profilers, set([]))

    options.profilers = 'list'
    test_tool._ParseProfilingOptions(options)
    self.assertEqual(test_tool._profilers, set([]))

    with shared_test_lib.TempDirectory() as temp_directory:
      options.profilers = 'processing'
      options.profiling_directory = temp_directory
      test_tool._ParseProfilingOptions(options)
      self.assertEqual(test_tool._profilers, set(['processing']))
      self.assertEqual(test_tool._profiling_directory, temp_directory)
      self.assertEqual(test_tool._profiling_sample_rate, 100)

    with self.assertRaises(errors.BadConfigOption):
      options.profiling_sample_rate = 'a'
      test_tool._ParseProfilingOptions(options)

    with self.assertRaises(errors.BadConfigOption):
      options.profiling_sample_rate = 100
      test_tool._ParseProfilingOptions(options)

    with self.assertRaises(errors.BadConfigOption):
      options.profiling_sample_rate = '/bogus'
      options.profiling_sample_rate = 100
      test_tool._ParseProfilingOptions(options)

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

  def testAddProfilingOptions(self):
    """Tests the AddProfilingOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog='tool_test.py', description='Test argument parser.',
        add_help=False, formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = tools.CLITool()
    test_tool.AddProfilingOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_PROFILING_OPTIONS)

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

  def testListProfilers(self):
    """Tests the ListProfilers function."""
    output_writer = test_lib.TestOutputWriter()
    cli_tool = tools.CLITool(output_writer=output_writer)

    cli_tool.ListProfilers()

    string = output_writer.ReadOutput()
    expected_string = (
        b'\n'
        b'********************************** Profilers '
        b'***********************************\n'
        b'       Name : Description\n'
        b'----------------------------------------'
        b'----------------------------------------\n')
    self.assertTrue(string.startswith(expected_string))

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

  def testParseNumericOption(self):
    """Tests the ParseNumericOption function."""
    output_writer = test_lib.TestOutputWriter()
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

    input_reader = tools.StdinInputReader(encoding='ascii')

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

    sys.stdin = original_stdin

  def testReadUtf8(self):
    """Tests the Read function with UTF-8 encoding."""
    original_stdin = sys.stdin
    sys.stdin = io.BytesIO(self._TEST_DATA)

    input_reader = tools.StdinInputReader()

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

    sys.stdin = original_stdin


class FileObjectOutputWriterTest(unittest.TestCase):
  """The unit test case for a file-like object output writer."""

  def testWriteAscii(self):
    """Tests the Write function with ASCII encoding."""
    output_writer = test_lib.TestOutputWriter(encoding='ascii')

    output_writer.Write('A first string\n')
    string = output_writer.ReadOutput()
    self.assertEqual(string, b'A first string\n')

    # Byte string with ASCII characters.
    output_writer.Write(b'A 2nd string\n')
    string = output_writer.ReadOutput()
    self.assertEqual(string, b'A 2nd string\n')

    # Unicode string with non-ASCII characters.
    output_writer.Write('þriðja string\n')
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

    output_writer.Write('A first string\n')
    string = output_writer.ReadOutput()
    self.assertEqual(string, b'A first string\n')

    # Byte string with ASCII characters.
    output_writer.Write(b'A 2nd string\n')
    string = output_writer.ReadOutput()
    self.assertEqual(string, b'A 2nd string\n')

    # Unicode string with non-ASCII characters.
    output_writer.Write('þriðja string\n')
    string = output_writer.ReadOutput()
    self.assertEqual(string, b'\xc3\xberi\xc3\xb0ja string\n')

    # Byte string with non-ASCII characters.
    with self.assertRaises(UnicodeDecodeError):
      # This fails because the byte string cannot be converted to
      # a Unicode string before the call to encode().
      output_writer.Write(b'\xc3\xberi\xc3\xb0ja string\n')


if __name__ == '__main__':
  unittest.main()
