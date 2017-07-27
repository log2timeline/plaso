#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the filter file CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import filter_file
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class FilterFileArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the filter file CLI arguments helper."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [-f FILE_FILTER]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  -f FILE_FILTER, --file_filter FILE_FILTER, --file-filter FILE_FILTER',
      (u'                        List of files to include for targeted '
       u'collection of'),
      (u'                        files to parse, one line per file path, '
       u'setup is'),
      (u'                        /path|file - where each element can contain '
       u'either a'),
      (u'                        variable set in the preprocessing stage or '
       u'a regular'),
      u'                        expression.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py', description=u'Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    filter_file.FilterFileArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.file_filter = self._GetTestFilePath([u'testdir', u'filter2.txt'])

    test_tool = tools.CLITool()
    filter_file.FilterFileArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._filter_file, options.file_filter)

    with self.assertRaises(errors.BadConfigObject):
      filter_file.FilterFileArgumentsHelper.ParseOptions(options, None)

    # TODO: improve test coverage.


if __name__ == '__main__':
  unittest.main()
