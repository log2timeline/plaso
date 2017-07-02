#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the date filters CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import date_filters
from plaso.filters import file_entry as file_entry_filters
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class DateFiltersArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the date filters CLI arguments helper."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--date-filter TYPE_START_END]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --date-filter TYPE_START_END, --date_filter TYPE_START_END',
      (u'                        Filter based on file entry date and time '
       u'ranges. This'),
      u'                        parameter is formatted as',
      (u'                        "TIME_VALUE,START_DATE_TIME,END_DATE_TIME" '
       u'where'),
      (u'                        TIME_VALUE defines which file entry '
       u'timestamp the'),
      (u'                        filter applies to e.g. atime, ctime, '
       u'crtime, bkup,'),
      u'                        etc. START_DATE_TIME and END_DATE_TIME define',
      (u'                        respectively the start and end of the date '
       u'time range.'),
      (u'                        A date time range requires at minimum start '
       u'or end to'),
      (u'                        time of the boundary and END defines the '
       u'end time.'),
      (u'                        Both timestamps be set. The date time '
       u'values are'),
      (u'                        formatted as: YYYY-MM-DD hh:mm:ss.######'
       u'[+-]##:##'),
      (u'                        Where # are numeric digits ranging from 0 '
       u'to 9 and the'),
      (u'                        seconds fraction can be either 3 or 6 '
       u'digits. The time'),
      (u'                        of day, seconds fraction and timezone '
       u'offset are'),
      (u'                        optional. The default timezone is UTC. '
       u'E.g. "atime,'),
      (u'                        2013-01-01 23:12:14, 2013-02-23". This '
       u'parameter can'),
      (u'                        be repeated as needed to add additional '
       u'date'),
      (u'                        boundaries, e.g. once for atime, once for '
       u'crtime, etc.'),
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py', description=u'Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    date_filters.DateFiltersArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.date_filters = [u'ctime,2012-05-25 15:59:00,2012-05-25 15:59:20']

    test_tool = tools.CLITool()

    with self.assertRaises(errors.BadConfigObject):
      date_filters.DateFiltersArgumentsHelper.ParseOptions(options, None)

    with self.assertRaises(errors.BadConfigObject):
      test_tool._filter_collection = None
      date_filters.DateFiltersArgumentsHelper.ParseOptions(options, test_tool)

    test_tool._filter_collection = (
        file_entry_filters.FileEntryFilterCollection())

    date_filters.DateFiltersArgumentsHelper.ParseOptions(options, test_tool)
    self.assertTrue(test_tool._filter_collection.HasFilters())

    with self.assertRaises(errors.BadConfigOption):
      options.date_filters = [u'ctime,2012-05-25 15:59:00']
      date_filters.DateFiltersArgumentsHelper.ParseOptions(options, test_tool)

    with self.assertRaises(errors.BadConfigOption):
      options.date_filters = [u'ctime,2012-05-25 15:59:00,2012-05-A5 15:59:20']
      date_filters.DateFiltersArgumentsHelper.ParseOptions(options, test_tool)


if __name__ == '__main__':
  unittest.main()
