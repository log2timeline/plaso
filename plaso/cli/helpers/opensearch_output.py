# -*- coding: utf-8 -*-
"""The OpenSearch output module CLI arguments helper."""

import getpass
import json
import os

from uuid import uuid4

from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.cli import logger
from plaso.lib import errors
from plaso.output import shared_opensearch


class OpenSearchOutputArgumentsHelper(interface.ArgumentsHelper):
  """OpenSearch output module CLI arguments helper."""

  NAME = 'opensearch'
  CATEGORY = 'output'
  DESCRIPTION = 'Argument helper for the OpenSearch output modules.'

  _DEFAULT_FIELDS = [
      'datetime', 'display_name', 'message', 'source_long', 'source_short',
      'tag', 'timestamp', 'timestamp_desc']

  _DEFAULT_FLUSH_INTERVAL = 1000
  _DEFAULT_INDEX_NAME = uuid4().hex
  _DEFAULT_PORT = 9200
  _DEFAULT_SERVER = '127.0.0.1'

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    argument_group.add_argument(
        '--index_name', '--index-name', dest='index_name', type=str,
        action='store', default=cls._DEFAULT_INDEX_NAME, metavar='NAME',
        help='Name of the index in OpenSearch.')

    argument_group.add_argument(
        '--flush_interval', '--flush-interval', dest='flush_interval', type=int,
        action='store', default=cls._DEFAULT_FLUSH_INTERVAL, metavar='INTERVAL',
        help='Events to queue up before bulk insert to OpenSearch.')

    argument_group.add_argument(
        '--opensearch-server', '--opensearch_server', '--server', dest='server',
        type=str, action='store', default=cls._DEFAULT_SERVER,
        metavar='HOSTNAME', help=(
            'Hostname or IP address of the OpenSearch server.'))

    argument_group.add_argument(
        '--opensearch-port', '--opensearch_port', '--port', dest='port',
        type=int, action='store', default=cls._DEFAULT_PORT, metavar='PORT',
        help='Port number of the OpenSearch server.')

    argument_group.add_argument(
        '--opensearch-user', '--opensearch_user', dest='opensearch_user',
        action='store', default=None, metavar='USERNAME', help=(
            'Username to use for OpenSearch authentication.'))

    argument_group.add_argument(
        '--opensearch-password', '--opensearch_password',
        dest='opensearch_password', action='store', default=None,
        metavar='PASSWORD', help=(
            'Password to use for OpenSearch authentication. WARNING: use '
            'with caution since this can expose the password to other users '
            'on the system. The password can also be set with the environment '
            'variable PLASO_OPENSEARCH_PASSWORD.'))

    argument_group.add_argument(
        '--opensearch-mappings', '--opensearch_mappings',
        dest='opensearch_mappings', action='store', default=None,
        metavar='PATH', help=(
            'Path to a file containing mappings for OpenSearch indexing.'))

    argument_group.add_argument(
        '--opensearch-url-prefix', '--opensearch_url_prefix',
        dest='opensearch_url_prefix', type=str, action='store', default=None,
        metavar='URL_PREFIX', help='URL prefix for OpenSearch.')

    argument_group.add_argument(
        '--use_ssl', '--use-ssl', dest='use_ssl', action='store_true',
        help='Enforces use of SSL/TLS.')

    argument_group.add_argument(
        '--ca_certificates_file_path', '--ca-certificates-file-path',
        dest='ca_certificates_file_path', action='store', type=str,
        default=None, metavar='PATH', help=(
            'Path to a file containing a list of root certificates to trust.'))

  @classmethod
  def ParseOptions(cls, options, output_module):  # pylint: disable=arguments-renamed
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      output_module (OutputModule): output module to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not isinstance(
        output_module, shared_opensearch.SharedOpenSearchOutputModule):
      raise errors.BadConfigObject(
          'Output module is not an instance of OpenSearchOutputModule')

    index_name = cls._ParseStringOption(
        options, 'index_name', default_value=cls._DEFAULT_INDEX_NAME)
    flush_interval = cls._ParseNumericOption(
        options, 'flush_interval', default_value=cls._DEFAULT_FLUSH_INTERVAL)

    mappings_file_path = cls._ParseStringOption(options, 'opensearch_mappings')
    opensearch_user = cls._ParseStringOption(options, 'opensearch_user')
    opensearch_password = cls._ParseStringOption(options, 'opensearch_password')
    use_ssl = getattr(options, 'use_ssl', False)

    ca_certificates_path = cls._ParseStringOption(
        options, 'ca_certificates_file_path')
    opensearch_url_prefix = cls._ParseStringOption(
        options, 'opensearch_url_prefix')

    if opensearch_password is None:
      opensearch_password = os.getenv('PLASO_OPENSEARCH_PASSWORD', None)

    if opensearch_password is not None:
      logger.warning(
          'Note that specifying your OpenSearch password via '
          '--opensearch_password or the environment PLASO_OPENSEARCH_PASSWORD '
          'can expose the password to other users on the system.')

    if opensearch_user is not None and opensearch_password is None:
      opensearch_password = getpass.getpass('Enter your OpenSearch password: ')

    server = cls._ParseStringOption(
        options, 'server', default_value=cls._DEFAULT_SERVER)
    port = cls._ParseNumericOption(
        options, 'port', default_value=cls._DEFAULT_PORT)

    output_module.SetServerInformation(server, port)

    output_module.SetIndexName(index_name)
    output_module.SetFlushInterval(flush_interval)

    output_module.SetUsername(opensearch_user)
    output_module.SetPassword(opensearch_password)
    output_module.SetUseSSL(use_ssl)
    output_module.SetCACertificatesPath(ca_certificates_path)
    output_module.SetURLPrefix(opensearch_url_prefix)

    if not mappings_file_path or not os.path.isfile(mappings_file_path):
      mappings_filename = output_module.MAPPINGS_FILENAME

      mappings_path = getattr(output_module, 'MAPPINGS_PATH', None)
      if mappings_path:
        mappings_file_path = os.path.join(mappings_path, mappings_filename)
      else:
        data_location = getattr(options, '_data_location', None) or 'data'
        mappings_file_path = os.path.join(data_location, mappings_filename)

    if not mappings_file_path or not os.path.isfile(mappings_file_path):
      raise errors.BadConfigOption(
          'No such OpenSearch mappings file: {0!s}.'.format(
              mappings_file_path))

    with open(mappings_file_path, 'r', encoding='utf-8') as file_object:
      mappings_json = json.load(file_object)

    output_module.SetMappings(mappings_json)


manager.ArgumentHelperManager.RegisterHelper(OpenSearchOutputArgumentsHelper)
