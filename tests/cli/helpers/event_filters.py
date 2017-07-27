#!/usr/bin/python
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

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = u'\n'.join([
      (u'usage: cli_helper.py [--slice DATE] [--slice_size SLICE_SIZE] '
       u'[--slicer]'),
      u'                     [FILTER]',
      u'',
      u'Test argument parser.',
      u'',
      u'positional arguments:',
      (u'  FILTER                A filter that can be used to filter the '
       u'dataset before'),
      (u'                        it is written into storage. More information '
       u'about the'),
      (u'                        filters and how to use them can be found '
       u'here:'),
      (u'                        '
       u'https://github.com/log2timeline/plaso/wiki/Filters'),
      u'',
      u'optional arguments:',
      (u'  --slice DATE          Create a time slice around a certain date. '
       u'This'),
      (u'                        parameter, if defined will display all '
       u'events that'),
      (u'                        happened X minutes before and after the '
       u'defined date.'),
      (u'                        X is controlled by the parameter '
       u'--slice_size but'),
      u'                        defaults to 5 minutes.',
      u'  --slice_size SLICE_SIZE, --slice-size SLICE_SIZE',
      (u'                        Defines the slice size. In the case of a '
       u'regular time'),
      (u'                        slice it defines the number of minutes the '
       u'slice size'),
      (u'                        should be. In the case of the --slicer it '
       u'determines'),
      (u'                        the number of events before and after a '
       u'filter match'),
      (u'                        has been made that will be included in the '
       u'result set.'),
      (u'                        The default value is 5]. See --slice or '
       u'--slicer for'),
      u'                        more details about this option.',
      (u'  --slicer              Create a time slice around every filter '
       u'match. This'),
      (u'                        parameter, if defined will save all X '
       u'events before'),
      (u'                        and after a filter match has been made. X '
       u'is defined'),
      u'                        by the --slice_size parameter.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py', description=u'Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    event_filters.EventFiltersArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.filter = u'event.timestamp == 0'

    test_tool = tools.CLITool()
    event_filters.EventFiltersArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._event_filter_expression, options.filter)
    self.assertIsNotNone(test_tool._event_filter)

    with self.assertRaises(errors.BadConfigObject):
      event_filters.EventFiltersArgumentsHelper.ParseOptions(options, None)

    # TODO: improve test coverage.


if __name__ == '__main__':
  unittest.main()
