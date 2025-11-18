#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the VFS back-end CLI arguments helper."""

import sys
import unittest

from plaso.cli import tools
from plaso.cli.helpers import vfs_backend
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class VFSBackEndArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the VFS back-end CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _PYTHON3_13_OR_LATER = sys.version_info[0:2] >= (3, 13)

  if _PYTHON3_13_OR_LATER:
    _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--vfs_back_end TYPE]

Test argument parser.

{0:s}:
  --vfs_back_end, --vfs-back-end TYPE
                        The preferred dfVFS back-end: "auto", "fsext",
                        "fsfat", "fshfs", "fsntfs", "tsk" or "vsgpt".
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  else:
    _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--vfs_back_end TYPE]

Test argument parser.

{0:s}:
  --vfs_back_end TYPE, --vfs-back-end TYPE
                        The preferred dfVFS back-end: "auto", "fsext",
                        "fsfat", "fshfs", "fsntfs", "tsk" or "vsgpt".
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = self._GetTestArgumentParser('cli_helper.py')

    vfs_backend.VFSBackEndArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.vfs_back_end = 'auto'

    test_tool = tools.CLITool()
    vfs_backend.VFSBackEndArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._vfs_back_end, options.vfs_back_end)

    with self.assertRaises(errors.BadConfigObject):
      vfs_backend.VFSBackEndArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
