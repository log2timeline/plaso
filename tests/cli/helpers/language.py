#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the language CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import language
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class LanguagergumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the language CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--language LANGUAGE]

Test argument parser.

optional arguments:
  --language LANGUAGE  The preferred language identifier for Windows Event Log
                       message strings. Use "--language list" to see a list of
                       available language identifiers. Note that formatting
                       will fall back on en-US (LCID 0x0409) if the preferred
                       language is not available in the database of message
                       string templates.
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    language.LanguageArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.preferred_language = 'is'

    test_tool = tools.CLITool()
    language.LanguageArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._preferred_language, options.preferred_language)

    with self.assertRaises(errors.BadConfigObject):
      language.LanguageArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
