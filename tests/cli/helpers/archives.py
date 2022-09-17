#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the archives CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import archives
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class ArchivesArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the archives CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--archives TYPES]

Test argument parser.

{0:s}:
  --archives TYPES  Define a list of archive and storage media image types for
                    which to process embedded file entries, such as TAR
                    (archive.tar) or ZIP (archive.zip). This is a comma
                    separated list where each entry is the name of an archive
                    type, such as "tar,zip". "all" indicates that all archive
                    types should be enabled. "none" disables processing file
                    entries embedded in archives. Use "--archives list" to
                    list the available archive types. WARNING: this can make
                    processing significantly slower.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    archives.ArchivesArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.archives = 'tar'

    test_tool = tools.CLITool()
    archives.ArchivesArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._archive_types_string, options.archives)

    with self.assertRaises(errors.BadConfigObject):
      archives.ArchivesArgumentsHelper.ParseOptions(options, None)

    with self.assertRaises(errors.BadConfigOption):
      options.archives = 'bogus'
      archives.ArchivesArgumentsHelper.ParseOptions(options, test_tool)


if __name__ == '__main__':
  unittest.main()
