#!/usr/bin/env python3
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

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--preferred_year YEAR] [--process_archives]
                     [--skip_compressed_streams]

Test argument parser.

{0:s}:
  --preferred_year YEAR, --preferred-year YEAR
                        When a format\'s timestamp does not include a year,
                        e.g. syslog, use this as the initial year instead of
                        attempting auto-detection.
  --process_archives, --process-archives
                        Process file entries embedded within archive files,
                        such as archive.tar and archive.zip. This can make
                        processing significantly slower. WARNING: this option
                        is deprecated use --archives=tar,zip instead.
  --skip_compressed_streams, --skip-compressed-streams
                        Skip processing file content within compressed
                        streams, such as syslog.gz and syslog.bz2.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
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

    self.assertIsNone(test_tool._preferred_year)
    self.assertFalse(test_tool._process_archives)
    self.assertTrue(test_tool._process_compressed_streams)

    with self.assertRaises(errors.BadConfigObject):
      extraction.ExtractionArgumentsHelper.ParseOptions(options, None)

    # TODO: improve test coverage.


if __name__ == '__main__':
  unittest.main()
