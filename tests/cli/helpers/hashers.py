#!/usr/bin/python
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

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--hashers HASHER_LIST]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --hashers HASHER_LIST',
      (u'                        Define a list of hashers to use by the tool. '
       u'This is a'),
      (u'                        comma separated list where each entry is the '
       u'name of a'),
      (u'                        hasher, such as "md5,sha256". "all" '
       u'indicates that all'),
      (u'                        hashers should be enabled. "none" '
       u'disables all'),
      (u'                        hashers. Use "--hashers list" or '
       u'"--info" to list the'),
      u'                        available hashers.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py', description=u'Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    hashers.HashersArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.hashers = u'sha1'

    test_tool = tools.CLITool()
    hashers.HashersArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._hasher_names_string, options.hashers)

    with self.assertRaises(errors.BadConfigObject):
      hashers.HashersArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
