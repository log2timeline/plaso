#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the view classes."""

import unittest

from plaso.cli import views

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class TestBaseTableView(views.BaseTableView):
  """Class that implements a table view for testing."""

  def Write(self, unused_output_writer):
    """Writes the table to the output writer.

    Args:
      output_writer: the output writer (instance of OutputWriter).
    """
    return


class BaseTableViewTests(shared_test_lib.BaseTestCase):
  """Tests for the table view interface class."""

  def testAddRow(self):
    """Tests the AddRow function."""
    table_view = TestBaseTableView(
        column_names=[u'one', u'two', u'three'])

    # Adding rows with the same number of values as columns is permitted.
    table_view.AddRow([u'1', u'2', u'3'])

    # Adding rows with a different number of values as columns is not permitted.
    with self.assertRaises(ValueError):
      table_view.AddRow([u'4', u'5'])

    table_view.AddRow([u'4', u'5', u'6'])

    table_view = TestBaseTableView()

    table_view.AddRow([u'1', u'2', u'3'])

    # Adding rows with the same number of values is permitted.
    table_view.AddRow([u'4', u'5', u'6'])

    # Adding rows with a different number of values is not permitted.
    with self.assertRaises(ValueError):
      table_view.AddRow([u'7', u'8'])


class CLITableViewTests(shared_test_lib.BaseTestCase):
  """Tests for the command line table view class."""

  def testWrite(self):
    """Tests the Write function."""
    output_writer = test_lib.TestOutputWriter()

    # Table with columns.
    table_view = views.CLITableView(
        column_names=[u'Name', u'Description'], title=u'Title')
    table_view.AddRow([u'First name', u'The first name in the table'])
    table_view.AddRow([u'Second name', u'The second name in the table'])

    table_view.Write(output_writer)
    string = output_writer.ReadOutput()
    expected_string = (
        b'\n'
        b'************************************ '
        b'Title '
        b'*************************************\n'
        b'       Name : Description\n'
        b'----------------------------------------'
        b'----------------------------------------\n'
        b' First name : The first name in the table\n'
        b'Second name : The second name in the table\n'
        b'----------------------------------------'
        b'----------------------------------------\n')

    # Splitting the string makes it easier to see differences.
    self.assertEqual(string.split(b'\n'), expected_string.split(b'\n'))

    # Table without columns.
    table_view = views.CLITableView(title=u'Title')
    table_view.AddRow([u'Name', u'The name in the table'])
    table_view.AddRow([u'Description', u'The description in the table'])

    table_view.Write(output_writer)
    string = output_writer.ReadOutput()
    expected_string = (
        b'\n'
        b'************************************ '
        b'Title '
        b'*************************************\n'
        b'       Name : The name in the table\n'
        b'Description : The description in the table\n'
        b'----------------------------------------'
        b'----------------------------------------\n')

    # Splitting the string makes it easier to see differences.
    self.assertEqual(string.split(b'\n'), expected_string.split(b'\n'))

    # TODO: add test without title.

    # Table with a too large title.
    # TODO: determine if this is the desired behavior.
    title = (
        u'In computer programming, a string is traditionally a sequence '
        u'of characters, either as a literal constant or as some kind of '
        u'variable.')
    table_view = views.CLITableView(
        column_names=[u'Name', u'Description'], title=title)
    table_view.AddRow([u'First name', u'The first name in the table'])
    table_view.AddRow([u'Second name', u'The second name in the table'])

    with self.assertRaises(RuntimeError):
      table_view.Write(output_writer)


class MarkdownTableViewTests(shared_test_lib.BaseTestCase):
  """Tests for the Markdown table view class."""

  def testWrite(self):
    """Tests the Write function."""
    output_writer = test_lib.TestOutputWriter()

    # Table with columns.
    table_view = views.MarkdownTableView(
        column_names=[u'Name', u'Description'], title=u'Title')
    table_view.AddRow([u'First name', u'The first name in the table'])
    table_view.AddRow([u'Second name', u'The second name in the table'])

    table_view.Write(output_writer)
    string = output_writer.ReadOutput()
    expected_string = (
        b'### Title\n'
        b'\n'
        b'Name | Description\n'
        b'--- | ---\n'
        b'First name | The first name in the table\n'
        b'Second name | The second name in the table\n'
        b'\n')

    # Splitting the string makes it easier to see differences.
    self.assertEqual(string.split(b'\n'), expected_string.split(b'\n'))

    # Table without columns.
    table_view = views.MarkdownTableView(title=u'Title')
    table_view.AddRow([u'Name', u'The name in the table'])
    table_view.AddRow([u'Description', u'The description in the table'])

    table_view.Write(output_writer)
    string = output_writer.ReadOutput()
    expected_string = (
        b'### Title\n'
        b'\n'
        b' | \n'
        b'--- | ---\n'
        b'Name | The name in the table\n'
        b'Description | The description in the table\n'
        b'\n')

    # Splitting the string makes it easier to see differences.
    self.assertEqual(string.split(b'\n'), expected_string.split(b'\n'))

    # TODO: add test without title.


if __name__ == '__main__':
  unittest.main()
