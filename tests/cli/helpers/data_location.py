#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the data location CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import data_location
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class DataLocationArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the data location CLI arguments helper."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--data PATH]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --data PATH  the location of the data files.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py', description=u'Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    data_location.DataLocationArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.data_location = self._GetTestFilePath([u'testdir'])

    test_tool = tools.CLITool()
    data_location.DataLocationArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._data_location, options.data_location)

    with self.assertRaises(errors.BadConfigObject):
      data_location.DataLocationArgumentsHelper.ParseOptions(options, None)

    # TODO: improve test coverage.


if __name__ == '__main__':
  unittest.main()
