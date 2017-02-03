#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Elastic Search output module CLI arguments helper."""

import argparse
import unittest

from plaso.cli.helpers import elastic_output
from plaso.lib import errors
from plaso.output import elastic

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class ElasticSearchOutputArgumentsHelperTest(
    test_lib.OutputModuleArgumentsHelperTest):
  """Tests the Elastic Search output module CLI arguments helper."""

  _EXPECTED_OUTPUT = u'\n'.join([
      u'usage: cli_helper.py [--index_name INDEX_NAME] [--doc_type DOC_TYPE]',
      u'                     [--flush_interval FLUSH_INTERVAL] [--raw_fields]',
      u'                     [--elastic_user ELASTIC_USER] [--server HOSTNAME]',
      u'                     [--port PORT]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --doc_type DOC_TYPE   Name of the document type that will be used in',
      u'                        ElasticSearch.',
      u'  --elastic_user ELASTIC_USER',
      (u'                        Username to use for Elasticsearch '
       u'authentication.'),
      u'  --flush_interval FLUSH_INTERVAL',
      u'                        Events to queue up before bulk insert to',
      u'                        ElasticSearch.',
      u'  --index_name INDEX_NAME',
      u'                        Name of the index in ElasticSearch.',
      u'  --port PORT           The port number of the server.',
      (u'  --raw_fields          Export string fields that will not be '
       u'analyzed by'),
      u'                        Lucene.',
      (u'  --server HOSTNAME     The hostname or server IP address of the '
       u'server.'),
      u''])

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'cli_helper.py',
        description=u'Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    elastic_output.ElasticSearchOutputArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    output_mediator = self._CreateOutputMediator()
    output_module = elastic.ElasticSearchOutputModule(output_mediator)
    elastic_output.ElasticSearchOutputArgumentsHelper.ParseOptions(
        options, output_module)

    with self.assertRaises(errors.BadConfigObject):
      elastic_output.ElasticSearchOutputArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
