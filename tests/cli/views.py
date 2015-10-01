#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the CLI view classes."""

import unittest

from plaso.cli import views

from tests.cli import test_lib


class CLITableViewTests(unittest.TestCase):
  """Tests for the 2 column command line table view class."""

  def testPrintFooter(self):
    """Tests the PrintFooter function."""
    output_writer = test_lib.TestOutputWriter()
    table_view = views.CLITableView(output_writer)

    table_view.PrintFooter()
    string = output_writer.ReadOutput()
    expected_string = (
        b'----------------------------------------'
        b'----------------------------------------\n')
    self.assertEqual(string, expected_string)

  def testPrintHeader(self):
    """Tests the PrintHeader function."""
    output_writer = test_lib.TestOutputWriter()
    table_view = views.CLITableView(output_writer)

    table_view.PrintHeader(u'Text')
    string = output_writer.ReadOutput()
    expected_string = (
        b'\n'
        b'************************************* '
        b'Text '
        b'*************************************\n')
    self.assertEqual(string, expected_string)

    # TODO: determine if this is the desired behavior.
    table_view.PrintHeader(u'')
    string = output_writer.ReadOutput()
    expected_string = (
        b'\n'
        b'*************************************** '
        b' '
        b'***************************************\n')
    self.assertEqual(string, expected_string)

    # TODO: determine if this is the desired behavior.
    table_view.PrintHeader(None)
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
    table_view.PrintHeader(expected_string[2:-2])
    string = output_writer.ReadOutput()
    self.assertEqual(string, expected_string)

  def testPrintRow(self):
    """Tests the PrintRow function."""
    output_writer = test_lib.TestOutputWriter()
    table_view = views.CLITableView(output_writer)

    table_view.PrintRow(u'Name', u'Description')
    string = output_writer.ReadOutput()
    expected_string = b'                     Name : Description\n'
    self.assertEqual(string, expected_string)

    table_view = views.CLITableView(output_writer, column_width=10)
    table_view.PrintRow(u'Name', u'Description')
    string = output_writer.ReadOutput()
    expected_string = b'      Name : Description\n'
    self.assertEqual(string, expected_string)

    with self.assertRaises(ValueError):
      table_view = views.CLITableView(output_writer, column_width=-10)

    with self.assertRaises(ValueError):
      table_view = views.CLITableView(output_writer, column_width=100)


if __name__ == '__main__':
  unittest.main()
