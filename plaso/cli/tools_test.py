#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the CLI tools classes."""

import io
import sys
import unittest

from plaso.cli import test_lib
from plaso.cli import tools


class CLIToolTest(test_lib.CLIToolTestCase):
  """Tests for the CLI tool base class."""

  def testPrintColumnValue(self):
    """Tests the PrintColumnValue function."""
    original_stdout = sys.stdout

    cli_tool = tools.CLITool()

    sys.stdout = io.BytesIO()
    cli_tool.PrintColumnValue(u'Name', u'Description')
    string = sys.stdout.getvalue()
    expected_string = b'                     Name : Description\n'
    self.assertEqual(string, expected_string)

    sys.stdout = io.BytesIO()
    cli_tool.PrintColumnValue(u'Name', u'Description', column_width=10)
    string = sys.stdout.getvalue()
    expected_string = b'      Name : Description\n'
    self.assertEqual(string, expected_string)

    sys.stdout = io.BytesIO()
    with self.assertRaises(ValueError):
      cli_tool.PrintColumnValue(u'Name', u'Description', column_width=-10)

    # TODO: determine if this is the desired behavior.
    sys.stdout = io.BytesIO()
    cli_tool.PrintColumnValue(u'Name', u'Description', column_width=100)
    string = sys.stdout.getvalue()
    expected_string = (
        b'                                                                     '
        b'                           Name : \n'
        b'                                                                     '
        b'                                  Description\n')
    self.assertEqual(string, expected_string)

    sys.stdout = original_stdout

  def testPrintHeader(self):
    """Tests the PrintHeader function."""
    original_stdout = sys.stdout

    cli_tool = tools.CLITool()

    sys.stdout = io.BytesIO()
    cli_tool.PrintHeader(u'Text')
    string = sys.stdout.getvalue()
    expected_string = (
        b'\n'
        b'************************************* '
        b'Text '
        b'*************************************\n')
    self.assertEqual(string, expected_string)

    sys.stdout = io.BytesIO()
    cli_tool.PrintHeader(u'Another Text', character=u'x')
    string = sys.stdout.getvalue()
    expected_string = (
        b'\n'
        b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx '
        b'Another Text '
        b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n')
    self.assertEqual(string, expected_string)

    # TODO: determine if this is the desired behavior.
    sys.stdout = io.BytesIO()
    cli_tool.PrintHeader(u'')
    string = sys.stdout.getvalue()
    expected_string = (
        b'\n'
        b'*************************************** '
        b' '
        b'***************************************\n')
    self.assertEqual(string, expected_string)

    # TODO: determine if this is the desired behavior.
    sys.stdout = io.BytesIO()
    cli_tool.PrintHeader(None)
    string = sys.stdout.getvalue()
    expected_string = (
        b'\n'
        b'************************************* '
        b'None '
        b'*************************************\n')
    self.assertEqual(string, expected_string)

    # TODO: determine if this is the desired behavior.
    sys.stdout = io.BytesIO()
    expected_string = (
        u'\n '
        u'In computer programming, a string is traditionally a sequence '
        u'of characters, either as a literal constant or as some kind of '
        u'variable. \n')
    cli_tool.PrintHeader(expected_string[2:-2])
    string = sys.stdout.getvalue()
    self.assertEqual(string, expected_string)

    sys.stdout = original_stdout

  def testPrintSeparatorLine(self):
    """Tests the PrintSeparatorLine function."""
    original_stdout = sys.stdout

    cli_tool = tools.CLITool()

    sys.stdout = io.BytesIO()
    cli_tool.PrintSeparatorLine()
    string = sys.stdout.getvalue()
    expected_string = (
        b'----------------------------------------'
        b'----------------------------------------\n')
    self.assertEqual(string, expected_string)

    sys.stdout = original_stdout


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


class StdoutOutputWriterTest(unittest.TestCase):
  """The unit test case for a stdout output writer."""

  def testWriteAscii(self):
    """Tests the Write function with ASCII encoding."""
    original_stdout = sys.stdout
    output_writer = tools.StdoutOutputWriter(encoding=u'ascii')

    sys.stdout = io.BytesIO()
    output_writer.Write(u'A first string\n')
    string = sys.stdout.getvalue()
    self.assertEqual(string, b'A first string\n')

    # Byte string with ASCII characters.
    sys.stdout = io.BytesIO()
    output_writer.Write(b'A 2nd string\n')
    string = sys.stdout.getvalue()
    self.assertEqual(string, b'A 2nd string\n')

    # Unicode string with non-ASCII characters.
    sys.stdout = io.BytesIO()
    output_writer.Write(u'þriðja string\n')
    string = sys.stdout.getvalue()
    self.assertEqual(string, b'?ri?ja string\n')

    # Byte string with non-ASCII characters.
    sys.stdout = io.BytesIO()
    with self.assertRaises(UnicodeDecodeError):
      # This fails because the byte string cannot be converted to
      # a Unicode string before the call to encode().
      output_writer.Write(b'\xc3\xberi\xc3\xb0ja string\n')

    sys.stdout = original_stdout

  def testWriteUtf8(self):
    """Tests the Write function with UTF-8 encoding."""
    original_stdout = sys.stdout
    output_writer = tools.StdoutOutputWriter()

    sys.stdout = io.BytesIO()
    output_writer.Write(u'A first string\n')
    string = sys.stdout.getvalue()
    self.assertEqual(string, b'A first string\n')

    # Byte string with ASCII characters.
    sys.stdout = io.BytesIO()
    output_writer.Write(b'A 2nd string\n')
    string = sys.stdout.getvalue()
    self.assertEqual(string, b'A 2nd string\n')

    # Unicode string with non-ASCII characters.
    sys.stdout = io.BytesIO()
    output_writer.Write(u'þriðja string\n')
    string = sys.stdout.getvalue()
    self.assertEqual(string, b'\xc3\xberi\xc3\xb0ja string\n')

    # Byte string with non-ASCII characters.
    sys.stdout = io.BytesIO()
    with self.assertRaises(UnicodeDecodeError):
      # This fails because the byte string cannot be converted to
      # a Unicode string before the call to encode().
      output_writer.Write(b'\xc3\xberi\xc3\xb0ja string\n')

    sys.stdout = original_stdout


if __name__ == '__main__':
  unittest.main()
