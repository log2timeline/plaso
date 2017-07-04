#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the extraction tool object."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli import extraction_tool

from tests.cli import test_lib


class ExtractionToolTest(test_lib.CLIToolTestCase):
  """Tests for the extraction tool object."""

  # pylint: disable=protected-access

  _EXPECTED_PERFORMANCE_OPTIONS = '\n'.join([
      'usage: extraction_tool_test.py [--buffer_size BUFFER_SIZE]',
      '                               [--queue_size QUEUE_SIZE]',
      '',
      'Test argument parser.',
      '',
      'optional arguments:',
      ('  --buffer_size BUFFER_SIZE, --buffer-size BUFFER_SIZE, '
       '--bs BUFFER_SIZE'),
      ('                        The buffer size for the output (defaults to '
       '196MiB).'),
      '  --queue_size QUEUE_SIZE, --queue-size QUEUE_SIZE',
      '                        The maximum number of queued items per worker',
      '                        (defaults to 125000)',
      ''])

  def testParsePerformanceOptions(self):
    """Tests the _ParsePerformanceOptions function."""
    test_tool = extraction_tool.ExtractionTool()

    options = test_lib.TestOptions()

    test_tool._ParsePerformanceOptions(options)

  def testAddPerformanceOptions(self):
    """Tests the AddPerformanceOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog='extraction_tool_test.py', description='Test argument parser.',
        add_help=False, formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = extraction_tool.ExtractionTool()
    test_tool.AddPerformanceOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_PERFORMANCE_OPTIONS)


if __name__ == '__main__':
  unittest.main()
