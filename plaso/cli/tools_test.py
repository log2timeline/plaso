#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the CLI tools classes."""

import argparse
import io
import sys
import unittest

from plaso.cli import test_lib
from plaso.cli import tools


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
        prog=u'tool_test.py',
        description=u'Test argument parser.',
        add_help=False)

    test_tool = tools.CLITool()
    test_tool.AddBasicOptions(argument_parser)

    output = argument_parser.format_help()
    self.assertEqual(output, self._EXPECTED_BASIC_OPTIONS)

  def testAddDataLocationOption(self):
    """Tests the AddDataLocationOption function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'tool_test.py',
        description=u'Test argument parser.',
        add_help=False)

    test_tool = tools.CLITool()
    test_tool.AddDataLocationOption(argument_parser)

    output = argument_parser.format_help()
    self.assertEqual(output, self._EXPECTED_DATA_OPTION)

  def testAddInformationalOptions(self):
    """Tests the AddInformationalOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'tool_test.py',
        description=u'Test argument parser.',
        add_help=False)

    test_tool = tools.CLITool()
    test_tool.AddInformationalOptions(argument_parser)

    output = argument_parser.format_help()
    self.assertEqual(output, self._EXPECTED_INFORMATIONAL_OPTIONS)

  def testAddTimezoneOption(self):
    """Tests the AddTimezoneOption function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'tool_test.py',
        description=u'Test argument parser.',
        add_help=False)

    test_tool = tools.CLITool()
    test_tool.AddTimezoneOption(argument_parser)

    output = argument_parser.format_help()
    self.assertEqual(output, self._EXPECTED_TIMEZONE_OPTION)

  def testPrintColumnValue(self):
    """Tests the PrintColumnValue function."""
    output_writer = test_lib.TestOutputWriter()
    cli_tool = tools.CLITool(output_writer=output_writer)

    cli_tool.PrintColumnValue(u'Name', u'Description')
    string = output_writer.ReadOutput()
    expected_string = b'                     Name : Description\n'
    self.assertEqual(string, expected_string)

    cli_tool.PrintColumnValue(u'Name', u'Description', column_width=10)
    string = output_writer.ReadOutput()
    expected_string = b'      Name : Description\n'
    self.assertEqual(string, expected_string)

    with self.assertRaises(ValueError):
      cli_tool.PrintColumnValue(u'Name', u'Description', column_width=-10)

    # TODO: determine if this is the desired behavior.
    cli_tool.PrintColumnValue(u'Name', u'Description', column_width=100)
    string = output_writer.ReadOutput()
    expected_string = (
        b'                                                                     '
        b'                           Name : \n'
        b'                                                                     '
        b'                                  Description\n')
    self.assertEqual(string, expected_string)

  def testPrintHeader(self):
    """Tests the PrintHeader function."""
    output_writer = test_lib.TestOutputWriter()
    cli_tool = tools.CLITool(output_writer=output_writer)

    cli_tool.PrintHeader(u'Text')
    string = output_writer.ReadOutput()
    expected_string = (
        b'\n'
        b'************************************* '
        b'Text '
        b'*************************************\n')
    self.assertEqual(string, expected_string)

    cli_tool.PrintHeader(u'Another Text', character=u'x')
    string = output_writer.ReadOutput()
    expected_string = (
        b'\n'
        b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx '
        b'Another Text '
        b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n')
    self.assertEqual(string, expected_string)

    # TODO: determine if this is the desired behavior.
    cli_tool.PrintHeader(u'')
    string = output_writer.ReadOutput()
    expected_string = (
        b'\n'
        b'*************************************** '
        b' '
        b'***************************************\n')
    self.assertEqual(string, expected_string)

    # TODO: determine if this is the desired behavior.
    cli_tool.PrintHeader(None)
    string = output_writer.ReadOutput()
    expected_string = (
        b'\n'
        b'************************************* '
        b'None '
        b'*************************************\n')
    self.assertEqual(string, expected_string)

    # TODO: determine if this is the desired behavior.
    expected_string = (
        u'\n '
        u'In computer programming, a string is traditionally a sequence '
        u'of characters, either as a literal constant or as some kind of '
        u'variable. \n')
    cli_tool.PrintHeader(expected_string[2:-2])
    string = output_writer.ReadOutput()
    self.assertEqual(string, expected_string)

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
