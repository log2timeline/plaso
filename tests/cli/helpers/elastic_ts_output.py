#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Elastic Timesketch output module CLI arguments helper."""

import argparse
import os
import unittest

from plaso.cli.helpers import elastic_ts_output
from plaso.lib import errors
from plaso.output import elastic_ts

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class ElasticTimesketchOutputArgumentsHelperTest(
    test_lib.OutputModuleArgumentsHelperTest):
  """Tests the Elastic Timesketch output module CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--index_name NAME] [--flush_interval INTERVAL]
                     [--raw_fields] [--additional_fields ADDITIONAL_FIELDS]
                     [--elastic_mappings PATH] [--elastic_user USERNAME]
                     [--elastic_password PASSWORD] [--use_ssl]
                     [--ca_certificates_file_path PATH]
                     [--elastic_url_prefix URL_PREFIX] [--server HOSTNAME]
                     [--port PORT] [--timeline_identifier IDENTIFIER]

Test argument parser.

optional arguments:
  --additional_fields ADDITIONAL_FIELDS, --additional-fields ADDITIONAL_FIELDS
                        Defines extra fields to be included in the output, in
                        addition to the default fields, which are datetime,
                        display_name, message, source_long, source_short, tag,
                        timestamp, timestamp_desc.
  --ca_certificates_file_path PATH, --ca-certificates-file-path PATH
                        Path to a file containing a list of root certificates
                        to trust.
  --elastic_mappings PATH, --elastic-mappings PATH
                        Path to a file containing mappings for Elasticsearch
                        indexing.
  --elastic_password PASSWORD, --elastic-password PASSWORD
                        Password to use for Elasticsearch authentication.
                        WARNING: use with caution since this can expose the
                        password to other users on the system. The password
                        can also be set with the environment variable
                        PLASO_ELASTIC_PASSWORD.
  --elastic_url_prefix URL_PREFIX, --elastic-url-prefix URL_PREFIX
                        URL prefix for elastic search.
  --elastic_user USERNAME, --elastic-user USERNAME
                        Username to use for Elasticsearch authentication.
  --flush_interval INTERVAL, --flush-interval INTERVAL
                        Events to queue up before bulk insert to
                        ElasticSearch.
  --index_name NAME, --index-name NAME
                        Name of the index in ElasticSearch.
  --port PORT           The port number of the server.
  --raw_fields, --raw-fields
                        Export string fields that will not be analyzed by
                        Lucene.
  --server HOSTNAME     The hostname or server IP address of the server.
  --timeline_identifier IDENTIFIER, --timeline-identifier IDENTIFIER
                        The identifier of the timeline in Timesketch.
  --use_ssl, --use-ssl  Enforces use of SSL/TLS.
"""

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    elastic_ts_output.ElasticTimesketchOutputArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()

    output_mediator = self._CreateOutputMediator()
    output_module = elastic_ts.ElasticTimesketchOutputModule(output_mediator)

    # The mappings file is /etc/timesketch/plaso.mappings by default which
    # does not exist on the CI test environment.
    with self.assertRaises(errors.BadConfigObject):
      elastic_ts_output.ElasticTimesketchOutputArgumentsHelper.ParseOptions(
          options, None)

    options.elastic_mappings = os.path.join('data', 'timesketch.mappings')
    elastic_ts_output.ElasticTimesketchOutputArgumentsHelper.ParseOptions(
        options, output_module)


if __name__ == '__main__':
  unittest.main()
