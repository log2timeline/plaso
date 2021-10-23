#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the language CLI arguments helper."""

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
usage: cli_helper.py [--language LANGUAGE_TAG]

Test argument parser.

{0:s}:
  --language LANGUAGE_TAG
                        The preferred language, which is used for extracting
                        and formatting Windows EventLog message strings. Use "
                        --language list" to see a list of supported language
                        tags. The en-US (LCID 0x0409) language is used as
                        fallback if preprocessing could not determine the
                        system language or no language information is
                        available in the winevt-rc.db database.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

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
