#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Timesketch output module CLI arguments helper."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli.helpers import timesketch_output
from plaso.lib import errors
from plaso.output import timesketch_out

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class MockTimesketchOutputModule(timesketch_out.TimesketchOutputModule):
  """Mock Timesketch output module for testing."""

  def __init__(self, output_mediator):
    """Initializes an output module object.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
    """
    # We deliberately don't call super here to prevent the call to
    # timesketch.create_app() raising an exception.
    # pylint: disable=super-init-not-called
    return


class TimesketchOutputArgumentsHelperTest(
    test_lib.OutputModuleArgumentsHelperTest):
  """Tests the Timesketch output module CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--name TIMELINE_NAME] [--index INDEX]
                     [--flush_interval FLUSH_INTERVAL]
                     [--doc_type DOCUMENT_TYPE] [--username USERNAME]

Test argument parser.

optional arguments:
  --doc_type DOCUMENT_TYPE
                        Name of the document type that will be used in
                        ElasticSearch.
  --flush_interval FLUSH_INTERVAL, --flush-interval FLUSH_INTERVAL
                        The number of events to queue up before sent in bulk
                        to Elasticsearch.
  --index INDEX         The name of the Elasticsearch index. Default: Generate
                        a random UUID
  --name TIMELINE_NAME, --timeline_name TIMELINE_NAME, --timeline-name TIMELINE_NAME
                        The name of the timeline in Timesketch. Default:
                        hostname if present in the storage file. If no
                        hostname is found then manual input is used.
  --username USERNAME   Username of a Timesketch user that will own the
                        timeline.
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    timesketch_output.TimesketchOutputArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    output_mediator = self._CreateOutputMediator()
    output_module = MockTimesketchOutputModule(output_mediator)
    timesketch_output.TimesketchOutputArgumentsHelper.ParseOptions(
        options, output_module)

    with self.assertRaises(errors.BadConfigObject):
      timesketch_output.TimesketchOutputArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
