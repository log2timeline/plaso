#!/usr/bin/python
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
usage: cli_helper.py [--worker-memory-limit SIZE] [--workers WORKERS]

Test argument parser.

optional arguments:
  --worker-memory-limit SIZE, --worker_memory_limit SIZE
                        Maximum amount of memory a worker process is allowed
                        to consume, where 0 represents no limit [defaults to 2
                        GiB].
  --workers WORKERS     The number of worker processes [defaults to available
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
