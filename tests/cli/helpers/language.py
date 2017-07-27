#!/usr/bin/python
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

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--language LANGUAGE]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      (u'  --language LANGUAGE  The preferred language identifier for Windows '
       u'Event Log'),
      (u'                       message strings. Use "--language list" to see '
       u'a list of'),
      (u'                       available language identifiers. Note that '
       u'formatting'),
      (u'                       will fall back on en-US (LCID 0x0409) if the '
       u'preferred'),
      (u'                       language is not available in the database of '
       u'message'),
      u'                       string templates.',
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py', description=u'Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    language.LanguageArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.preferred_language = u'is'

    test_tool = tools.CLITool()
    language.LanguageArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._preferred_language, options.preferred_language)

    with self.assertRaises(errors.BadConfigObject):
      language.LanguageArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
