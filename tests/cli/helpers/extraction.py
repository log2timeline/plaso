#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the extraction CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import extraction
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class ExtractionArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the extraction CLI arguments helper."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--preferred_year YEAR] [-p] [--process_archives]',
      u'                     [--skip_compressed_streams]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --preferred_year YEAR, --preferred-year YEAR',
      (u'                        When a format\'s timestamp does not include '
       u'a year,'),
      (u'                        e.g. syslog, use this as the initial year '
       u'instead of'),
      u'                        attempting auto-detection.',
      u'  --process_archives, --process-archives',
      (u'                        Process file entries embedded within archive '
       u'files,'),
      (u'                        such as archive.tar and archive.zip. This '
       u'can make'),
      u'                        processing significantly slower.',
      u'  --skip_compressed_streams, --skip-compressed-streams',
      u'                        Skip processing file content within compressed',
      u'                        streams, such as syslog.gz and syslog.bz2.',
      (u'  -p, --preprocess      Turn on preprocessing. Preprocessing is '
       u'turned on by'),
      (u'                        default when parsing image files, however if '
       u'a mount'),
      (u'                        point is being parsed then this parameter '
       u'needs to be'),
      u'                        set manually.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py', description=u'Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    extraction.ExtractionArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    test_tool = tools.CLITool()
    extraction.ExtractionArgumentsHelper.ParseOptions(options, test_tool)

    self.assertFalse(test_tool._force_preprocessing)
    self.assertIsNone(test_tool._preferred_year)
    self.assertFalse(test_tool._process_archives)
    self.assertTrue(test_tool._process_compressed_streams)

    with self.assertRaises(errors.BadConfigObject):
      extraction.ExtractionArgumentsHelper.ParseOptions(options, None)

    # TODO: improve test coverage.


if __name__ == '__main__':
  unittest.main()
