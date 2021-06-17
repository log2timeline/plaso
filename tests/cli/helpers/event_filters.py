#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event filters CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import event_filters
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class EventFiltersArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the event filters CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--slice DATE_TIME] [--slice_size SLICE_SIZE] [--slicer]
                     [FILTER]

Test argument parser.

positional arguments:
  FILTER                A filter that can be used to filter the dataset before
                        it is written into storage. More information about the
                        filters and how to use them can be found here: https:/
                        /plaso.readthedocs.io/en/latest/sources/user/Event-
                        filters.html

{0:s}:
  --slice DATE_TIME     Date and time to create a time slice around. This
                        parameter, if defined, will display all events that
                        happened X minutes before and after the defined date,
                        where X is controlled by the --slice_size option,
                        which is 5 minutes by default. The date and time must
                        be specified in ISO 8601 format including time zone
                        offset, for example: 20200619T20:09:23+02:00.
  --slice_size SLICE_SIZE, --slice-size SLICE_SIZE
                        Defines the slice size. In the case of a regular time
                        slice it defines the number of minutes the slice size
                        should be. In the case of the --slicer it determines
                        the number of events before and after a filter match
                        has been made that will be included in the result set.
                        The default value is 5. See --slice or --slicer for
                        more details about this option.
  --slicer              Create a time slice around every filter match. This
                        parameter, if defined will save all X events before
                        and after a filter match has been made. X is defined
                        by the --slice_size parameter.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    event_filters.EventFiltersArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)

    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.filter = 'event.timestamp == 0'
    options.slice = '2020-06-13T06:33:10'
    options.slicer = False

    test_tool = tools.CLITool()
    event_filters.EventFiltersArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._event_filter_expression, options.filter)
    self.assertIsNotNone(test_tool._event_filter)

    with self.assertRaises(errors.BadConfigObject):
      event_filters.EventFiltersArgumentsHelper.ParseOptions(options, None)

    options.filter = 'BOGUS'

    with self.assertRaises(errors.BadConfigOption):
      event_filters.EventFiltersArgumentsHelper.ParseOptions(options, test_tool)

    options.filter = 'event.timestamp == 0'
    options.slice = '2020-06-13 06:33:10'

    with self.assertRaises(errors.BadConfigOption):
      event_filters.EventFiltersArgumentsHelper.ParseOptions(options, test_tool)

    options.slice = 'YEAR-06-13T06:33:10'

    with self.assertRaises(errors.BadConfigOption):
      event_filters.EventFiltersArgumentsHelper.ParseOptions(options, test_tool)

    options.slice = '2020-06-13T06:33:10'
    options.slicer = True

    with self.assertRaises(errors.BadConfigOption):
      event_filters.EventFiltersArgumentsHelper.ParseOptions(options, test_tool)

    # TODO: improve test coverage.


if __name__ == '__main__':
  unittest.main()
