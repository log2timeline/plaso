#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the OpenSearch output module CLI arguments helper."""

import argparse
import unittest

from plaso.cli.helpers import opensearch_output
from plaso.lib import errors
from plaso.output import opensearch

from tests.cli import test_lib as cli_test_lib
from tests.cli.helpers import test_lib


class OpenSearchOutputArgumentsHelperTest(
    test_lib.OutputModuleArgumentsHelperTest):
  """Tests the OpenSearch output module CLI arguments helper."""

  # pylint: disable=no-member,protected-access

  _EXPECTED_OUTPUT = """\
usage: cli_helper.py [--index_name NAME] [--flush_interval INTERVAL]
                     [--opensearch-server HOSTNAME] [--opensearch-port PORT]
                     [--opensearch-user USERNAME]
                     [--opensearch-password PASSWORD]
                     [--opensearch-mappings PATH]
                     [--opensearch-url-prefix URL_PREFIX] [--use_ssl]
                     [--ca_certificates_file_path PATH]

Test argument parser.

{0:s}:
  --ca_certificates_file_path PATH, --ca-certificates-file-path PATH
                        Path to a file containing a list of root certificates
                        to trust.
  --flush_interval INTERVAL, --flush-interval INTERVAL
                        Events to queue up before bulk insert to OpenSearch.
  --index_name NAME, --index-name NAME
                        Name of the index in OpenSearch.
  --opensearch-mappings PATH, --opensearch_mappings PATH
                        Path to a file containing mappings for OpenSearch
                        indexing.
  --opensearch-password PASSWORD, --opensearch_password PASSWORD
                        Password to use for OpenSearch authentication.
                        WARNING: use with caution since this can expose the
                        password to other users on the system. The password
                        can also be set with the environment variable
                        PLASO_OPENSEARCH_PASSWORD.
  --opensearch-port PORT, --opensearch_port PORT, --port PORT
                        Port number of the OpenSearch server.
  --opensearch-server HOSTNAME, --opensearch_server HOSTNAME, --server HOSTNAME
                        Hostname or IP address of the OpenSearch server.
  --opensearch-url-prefix URL_PREFIX, --opensearch_url_prefix URL_PREFIX
                        URL prefix for OpenSearch.
  --opensearch-user USERNAME, --opensearch_user USERNAME
                        Username to use for OpenSearch authentication.
  --use_ssl, --use-ssl  Enforces use of SSL/TLS.
""".format(cli_test_lib.ARGPARSE_OPTIONS)

  def testAddArguments(self):
    """Tests the AddArguments function."""
    argument_parser = argparse.ArgumentParser(
        prog='cli_helper.py',
        description='Test argument parser.', add_help=False,
        formatter_class=cli_test_lib.SortedArgumentsHelpFormatter)

    opensearch_output.OpenSearchOutputArgumentsHelper.AddArguments(
        argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options._data_location = 'data'

    output_module = opensearch.OpenSearchOutputModule()
    opensearch_output.OpenSearchOutputArgumentsHelper.ParseOptions(
        options, output_module)

    with self.assertRaises(errors.BadConfigObject):
      opensearch_output.OpenSearchOutputArgumentsHelper.ParseOptions(
          options, None)


if __name__ == '__main__':
  unittest.main()
