#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the ZeroMQ CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli import tools
from plaso.cli.helpers import zeromq
from plaso.lib import errors

from tests.cli import test_lib as cli_test_lib


class ZeroMQArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for the ZeroMQ CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--disable_zeromq]

Test argument parser.

optional arguments:
  --disable_zeromq, --disable-zeromq
                        Disable queueing using ZeroMQ. A Multiprocessing queue
                        will be used instead.
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py', description='Test argument parser.',
        add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    zeromq.ZeroMQArgumentsHelper.AddArguments(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    test_tool = tools.CLITool()
    zeromq.ZeroMQArgumentsHelper.ParseOptions(options, test_tool)

    with self.assertRaises(errors.BadConfigObject):
      zeromq.ZeroMQArgumentsHelper.ParseOptions(options, None)


if __name__ == '__main__':
  unittest.main()
