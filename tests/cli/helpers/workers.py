#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the worker processes CLI arguments helper."""

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
usage: cli_helper.py [--worker_memory_limit SIZE] [--worker_timeout MINUTES]
                     [--workers WORKERS]

Test argument parser.

{0:s}:
  --worker_memory_limit SIZE, --worker-memory-limit SIZE
                        Maximum amount of memory (data segment and shared
                        memory) a worker process is allowed to consume in
                        bytes, where 0 represents no limit. The default limit
                        is 2147483648 (2 GiB). If a worker process exceeds
                        this limit it is killed by the main (foreman) process.
  --worker_timeout MINUTES, --worker-timeout MINUTES
                        Number of minutes before a worker process that is not
                        providing status updates is considered inactive. The
                        default timeout is 15.0 minutes. If a worker process
                        exceeds this timeout it is killed by the main
                        (foreman) process.
  --workers WORKERS     Number of worker processes. The default is the number
                        of available system CPUs minus one, for the main
                        (foreman) process.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

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
