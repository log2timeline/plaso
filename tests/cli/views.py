#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the view classes."""

import sys
import unittest

from plaso.cli import views

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class TestBaseTableView(views.BaseTableView):
  """Class that implements a table view for testing."""

  # pylint: disable=unused-argument
  def Write(self, output_writer):
    """Writes the table to the output writer.

    Args:
      output_writer (OutputWriter): output writer.
    """
    return


class BaseTableViewTests(shared_test_lib.BaseTestCase):
  """Tests for the table view interface class."""

  def testAddRow(self):
    """Tests the AddRow function."""
    table_view = TestBaseTableView(
        column_names=['one', 'two', 'three'])

    # Adding rows with the same number of values as columns is permitted.
    table_view.AddRow(['1', '2', '3'])

    # Adding rows with a different number of values as columns is not permitted.
    with self.assertRaises(ValueError):
      table_view.AddRow(['4', '5'])

    table_view.AddRow(['4', '5', '6'])

    table_view = TestBaseTableView()

    table_view.AddRow(['1', '2', '3'])

    # Adding rows with the same number of values is permitted.
    table_view.AddRow(['4', '5', '6'])

    # Adding rows with a different number of values is not permitted.
    with self.assertRaises(ValueError):
      table_view.AddRow(['7', '8'])


class CLITableViewTests(shared_test_lib.BaseTestCase):
  """Tests for the command line table view class."""

  _EXPECTED_OUTPUT1 = """\

************************************ Title *************************************
       Name : Description
--------------------------------------------------------------------------------
 First name : The first name in the table
Second name : The second name in the table
--------------------------------------------------------------------------------
"""

  _EXPECTED_OUTPUT2 = """\

************************************ Title *************************************
       Name : The name in the table
Description : The description in the table
--------------------------------------------------------------------------------
"""

  def testWrite(self):
    """Tests the Write function."""
    output_writer = test_lib.TestOutputWriter()

    # Table with columns.
    table_view = views.CLITableView(
        column_names=['Name', 'Description'], title='Title')
    table_view.AddRow(['First name', 'The first name in the table'])
    table_view.AddRow(['Second name', 'The second name in the table'])

    table_view.Write(output_writer)
    string = output_writer.ReadOutput()

    # Splitting the string makes it easier to see differences.
    self.assertEqual(string.split('\n'), self._EXPECTED_OUTPUT1.split('\n'))

    # Table without columns.
    table_view = views.CLITableView(title='Title')
    table_view.AddRow(['Name', 'The name in the table'])
    table_view.AddRow(['Description', 'The description in the table'])

    table_view.Write(output_writer)
    string = output_writer.ReadOutput()

    # Splitting the string makes it easier to see differences.
    self.assertEqual(string.split('\n'), self._EXPECTED_OUTPUT2.split('\n'))

    # TODO: add test without title.

    # Table with a too large title.
    # TODO: determine if this is the desired behavior.
    title = (
        'In computer programming, a string is traditionally a sequence '
        'of characters, either as a literal constant or as some kind of '
        'variable.')
    table_view = views.CLITableView(
        column_names=['Name', 'Description'], title=title)
    table_view.AddRow(['First name', 'The first name in the table'])
    table_view.AddRow(['Second name', 'The second name in the table'])

    with self.assertRaises(RuntimeError):
      table_view.Write(output_writer)


class CLITabularTableView(shared_test_lib.BaseTestCase):
  """Tests for the command line tabular table view class."""

  def testWrite(self):
    """Tests the Write function."""
    output_writer = test_lib.TestOutputWriter()

    table_view = views.CLITabularTableView(
        column_names=['Name', 'Description'])
    table_view.AddRow(['First name', 'The first name in the table'])
    table_view.AddRow(['Second name', 'The second name in the table'])

    table_view.Write(output_writer)
    string = output_writer.ReadOutput()

    expected_strings = [
        'Name            Description',
        'First name      The first name in the table',
        'Second name     The second name in the table',
        '']

    if not sys.platform.startswith('win'):
      expected_strings[0] = '\x1b[1mName            Description\x1b[0m'

    self.assertEqual(string.split('\n'), expected_strings)


class MarkdownTableViewTests(shared_test_lib.BaseTestCase):
  """Tests for the Markdown table view class."""

  _EXPECTED_OUTPUT1 = """\
### Title

Name | Description
--- | ---
First name | The first name in the table
Second name | The second name in the table

"""

  def testWrite(self):
    """Tests the Write function."""
    output_writer = test_lib.TestOutputWriter()

    # Table with columns.
    table_view = views.MarkdownTableView(
        column_names=['Name', 'Description'], title='Title')
    table_view.AddRow(['First name', 'The first name in the table'])
    table_view.AddRow(['Second name', 'The second name in the table'])

    table_view.Write(output_writer)
    string = output_writer.ReadOutput()

    # Splitting the string makes it easier to see differences.
    self.assertEqual(string.split('\n'), self._EXPECTED_OUTPUT1.split('\n'))

    # Table without columns.
    table_view = views.MarkdownTableView(title='Title')
    table_view.AddRow(['Name', 'The name in the table'])
    table_view.AddRow(['Description', 'The description in the table'])

    table_view.Write(output_writer)
    string = output_writer.ReadOutput()
    expected_string = (
        '### Title\n'
        '\n'
        '<table>\n'
        '<tr><th nowrap style="text-align:left;vertical-align:top">Name</th>'
        '<td>The name in the table</td></tr>\n'
        '<tr><th nowrap style="text-align:left;vertical-align:top">Description'
        '</th><td>The description in the table</td></tr>\n'
        '</table>\n'
        '\n')

    # Splitting the string makes it easier to see differences.
    self.assertEqual(string.split('\n'), expected_string.split('\n'))

    # TODO: add test without title.


if __name__ == '__main__':
  unittest.main()
