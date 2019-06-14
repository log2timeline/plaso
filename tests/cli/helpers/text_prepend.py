#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the text prepend CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import text_prepend
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class TextPrependArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the text prepend CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [-t TEXT]

Test argument parser.

optional arguments:
  -t TEXT, --text TEXT  Define a free form text string that is prepended to
                        each path to make it easier to distinguish one record
                        from another in a timeline (like c:\\, or host_w_c:\\)
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    text_prepend.TextPrependArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.text_prepend = 'host_w_c:\\'

    test_tool = tools.CLITool()
    text_prepend.TextPrependArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._text_prepend, options.text_prepend)

    with self.assertRaises(errors.BadConfigObject):
      text_prepend.TextPrependArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
