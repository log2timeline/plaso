#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the process resources CLI arguments helper."""

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import process_resources
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class ProcessResourcesArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the process resources CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--process_memory_limit SIZE]

Test argument parser.

{0:s}:
  --process_memory_limit SIZE, --process-memory-limit SIZE
                        Maximum amount of memory (data segment) a process is
                        allowed to allocate in bytes, where 0 represents no
                        limit. The default limit is 4294967296 (4 GiB). This
                        applies to both the main (foreman) process and the
                        worker processes. This limit is enforced by the
                        operating system and will supersede the worker memory
                        limit (--worker_memory_limit).
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    process_resources.ProcessResourcesArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    test_tool = tools.CLITool()
    process_resources.ProcessResourcesArgumentsHelper.ParseOptions(
        options, test_tool)

    with self.assertRaises(errors.BadConfigObject):
      process_resources.ProcessResourcesArgumentsHelper.ParseOptions(
          options, None)

    with self.assertRaises(errors.BadConfigOption):
      options.process_memory_limit = 'bogus'
      process_resources.ProcessResourcesArgumentsHelper.ParseOptions(
          options, test_tool)

    with self.assertRaises(errors.BadConfigOption):
      options.process_memory_limit = -1
      process_resources.ProcessResourcesArgumentsHelper.ParseOptions(
          options, test_tool)


if __name__ == '__main__':
  unittest.main()
