#!/usr/bin/env python3
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

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--date-filter TYPE_START_END]

Test argument parser.

{0:s}:
  --date-filter TYPE_START_END, --date_filter TYPE_START_END
                        Filter based on file entry date and time ranges. This
                        parameter is formatted as
                        "TIME_VALUE,START_DATE_TIME,END_DATE_TIME" where
                        TIME_VALUE defines which file entry timestamp the
                        filter applies to e.g. atime, ctime, crtime, bkup,
                        etc. START_DATE_TIME and END_DATE_TIME define
                        respectively the start and end of the date time range.
                        A date time range requires at minimum start or end to
                        time of the boundary and END defines the end time.
                        Both timestamps be set. The date time values are
                        formatted as: YYYY-MM-DD hh:mm:ss.######[+-]##:##
                        Where # are numeric digits ranging from 0 to 9 and the
                        seconds fraction can be either 3 or 6 digits. The time
                        of day, seconds fraction and time zone offset are
                        optional. The default time zone is UTC. E.g. "atime,
                        2013-01-01 23:12:14, 2013-02-23". This parameter can
                        be repeated as needed to add additional date
                        boundaries, e.g. once for atime, once for crtime, etc.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    date_filters.DateFiltersArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.date_filters = ['ctime,2012-05-25 15:59:00,2012-05-25 15:59:20']

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
      options.date_filters = ['ctime,2012-05-25 15:59:00']
      date_filters.DateFiltersArgumentsHelper.ParseOptions(options, test_tool)

    with self.assertRaises(errors.BadConfigOption):
      options.date_filters = ['ctime,2012-05-25 15:59:00,2012-05-A5 15:59:20']
      date_filters.DateFiltersArgumentsHelper.ParseOptions(options, test_tool)


if __name__ == '__main__':
  unittest.main()
