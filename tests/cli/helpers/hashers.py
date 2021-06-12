#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the hashers CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import hashers
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class HashersArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the hashers CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--hasher_file_size_limit SIZE] [--hashers HASHER_LIST]

Test argument parser.

{0:s}:
  --hasher_file_size_limit SIZE, --hasher-file-size-limit SIZE
                        Define the maximum file size in bytes that hashers
                        should process. Any larger file will be skipped. A
                        size of 0 represents no limit.
  --hashers HASHER_LIST
                        Define a list of hashers to use by the tool. This is a
                        comma separated list where each entry is the name of a
                        hasher, such as "md5,sha256". "all" indicates that all
                        hashers should be enabled. "none" disables all
                        hashers. Use "--hashers list" or "--info" to list the
                        available hashers.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    hashers.HashersArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.hashers = 'sha1'
    options.hasher_file_size_limit = 0

    test_tool = tools.CLITool()
    hashers.HashersArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._hasher_names_string, options.hashers)

    with self.assertRaises(errors.BadConfigObject):
      hashers.HashersArgumentsHelper.ParseOptions(options, None)

    with self.assertRaises(errors.BadConfigOption):
      options.hasher_file_size_limit = 'bogus'
      hashers.HashersArgumentsHelper.ParseOptions(options, test_tool)

    with self.assertRaises(errors.BadConfigOption):
      options.hasher_file_size_limit = -1
      hashers.HashersArgumentsHelper.ParseOptions(options, test_tool)


if __name__ == '__main__':
  unittest.main()
