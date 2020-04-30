#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the VFS back-end CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import vfs_backend
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class VFSBackEndArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the VFS back-end CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--vfs_back_end TYPE]

Test argument parser.

optional arguments:
  --vfs_back_end TYPE, --vfs-back-end TYPE
                        The preferred dfVFS back-end: "auto" or "tsk".
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    vfs_backend.VFSBackEndArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.vfs_backend = 'auto'

    test_tool = tools.CLITool()
    vfs_backend.VFSBackEndArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._vfs_backend, options.vfs_backend)

    with self.assertRaises(errors.BadConfigObject):
      vfs_backend.VFSBackEndArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
