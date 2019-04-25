#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the worker processes CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import workers
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class WorkersArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the worker processes CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--worker_memory_limit SIZE] [--workers WORKERS]

Test argument parser.

optional arguments:
  --worker_memory_limit SIZE, --worker-memory-limit SIZE
                        Maximum amount of memory (data segment and shared
                        memory) a worker process is allowed to consume in
                        bytes, where 0 represents no limit. The default limit
                        is 2147483648 (2 GiB). If a worker process exceeds
                        this limit is is killed by the main (foreman) process.
  --workers WORKERS     Number of worker processes [defaults to available
                        system CPUs minus one].
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    workers.WorkersArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.workers = 0

    test_tool = tools.CLITool()
    workers.WorkersArgumentsHelper.ParseOptions(options, test_tool)

    self.assertEqual(test_tool._number_of_extraction_workers, options.workers)

    with self.assertRaises(errors.BadConfigObject):
      workers.WorkersArgumentsHelper.ParseOptions(options, None)

    with self.assertRaises(errors.BadConfigOption):
      options.workers = 'bogus'
      workers.WorkersArgumentsHelper.ParseOptions(options, test_tool)

    with self.assertRaises(errors.BadConfigOption):
      options.workers = -1
      workers.WorkersArgumentsHelper.ParseOptions(options, test_tool)

    with self.assertRaises(errors.BadConfigOption):
      options.worker_memory_limit = 'bogus'
      workers.WorkersArgumentsHelper.ParseOptions(options, test_tool)

    with self.assertRaises(errors.BadConfigOption):
      options.worker_memory_limit = -1
      workers.WorkersArgumentsHelper.ParseOptions(options, test_tool)


if __name__ == '__main__':
  unittest.main()
