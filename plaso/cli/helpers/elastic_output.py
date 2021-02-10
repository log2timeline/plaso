# -*- coding: utf-8 -*-
"""The Elastic Search output module CLI arguments helper."""

import getpass
import json
import os

from uuid import uuid4

from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.cli.helpers import server_config
from plaso.cli import logger
from plaso.lib import errors
from plaso.output import elastic
from plaso.output import shared_elastic


class ElasticSearchServerArgumentsHelper(server_config.ServerArgumentsHelper):
  """Elastic Search server CLI arguments helper."""

  _DEFAULT_SERVER = '127.0.0.1'
  _DEFAULT_PORT = 9200


class ElasticSearchOutputArgumentsHelper(interface.ArgumentsHelper):
  """Elastic Search output module CLI arguments helper."""

  NAME = 'elastic'
  CATEGORY = 'output'
  DESCRIPTION = 'Argument helper for the Elastic Search output modules.'

  _DEFAULT_INDEX_NAME = uuid4().hex
  _DEFAULT_FLUSH_INTERVAL = 1000
  _DEFAULT_RAW_FIELDS = False

  _DEFAULT_FIELDS = [
      'datetime', 'display_name', 'message', 'source_long', 'source_short',
      'tag', 'timestamp', 'timestamp_desc']

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
        help='Name of the index in ElasticSearch.')

    argument_group.add_argument(
        '--flush_interval', '--flush-interval', dest='flush_interval', type=int,
        action='store', default=cls._DEFAULT_FLUSH_INTERVAL, metavar='INTERVAL',
        help='Events to queue up before bulk insert to ElasticSearch.')

    argument_group.add_argument(
        '--raw_fields', '--raw-fields', dest='raw_fields', action='store_true',
        default=cls._DEFAULT_RAW_FIELDS, help=(
            'Export string fields that will not be analyzed by Lucene.'))

    default_fields = ', '.join(cls._DEFAULT_FIELDS)
    argument_group.add_argument(
        '--additional_fields', '--additional-fields', dest='additional_fields',
        type=str, action='store', default='', help=(
            'Defines extra fields to be included in the output, in addition to '
            'the default fields, which are {0:s}.'.format(default_fields)))

    argument_group.add_argument(
        '--elastic_mappings', '--elastic-mappings', dest='elastic_mappings',
        action='store', default=None, metavar='PATH', help=(
            'Path to a file containing mappings for Elasticsearch indexing.'))

    argument_group.add_argument(
        '--elastic_user', '--elastic-user', dest='elastic_user', action='store',
        default=None, metavar='USERNAME', help=(
            'Username to use for Elasticsearch authentication.'))

    argument_group.add_argument(
        '--elastic_password', '--elastic-password', dest='elastic_password',
        action='store', default=None, metavar='PASSWORD', help=(
            'Password to use for Elasticsearch authentication. WARNING: use '
            'with caution since this can expose the password to other users '
            'on the system. The password can also be set with the environment '
            'variable PLASO_ELASTIC_PASSWORD. '))

    argument_group.add_argument(
        '--use_ssl', '--use-ssl', dest='use_ssl', action='store_true',
        help='Enforces use of SSL/TLS.')

    argument_group.add_argument(
        '--ca_certificates_file_path', '--ca-certificates-file-path',
        dest='ca_certificates_file_path', action='store', type=str,
        default=None, metavar='PATH', help=(
            'Path to a file containing a list of root certificates to trust.'))

    argument_group.add_argument(
        '--elastic_url_prefix', '--elastic-url-prefix',
        dest='elastic_url_prefix', type=str, action='store', default=None,
        metavar='URL_PREFIX', help='URL prefix for elastic search.')

    ElasticSearchServerArgumentsHelper.AddArguments(argument_group)

  # pylint: disable=arguments-differ
  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      output_module (OutputModule): output module to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not isinstance(
        output_module, shared_elastic.SharedElasticsearchOutputModule):
      raise errors.BadConfigObject(
          'Output module is not an instance of ElasticsearchOutputModule')

    index_name = cls._ParseStringOption(
        options, 'index_name', default_value=cls._DEFAULT_INDEX_NAME)
    flush_interval = cls._ParseNumericOption(
        options, 'flush_interval', default_value=cls._DEFAULT_FLUSH_INTERVAL)

    fields = ','.join(cls._DEFAULT_FIELDS)
    additional_fields = cls._ParseStringOption(options, 'additional_fields')

    if additional_fields:
      fields = ','.join([fields, additional_fields])

    mappings_file_path = cls._ParseStringOption(options, 'elastic_mappings')
    elastic_user = cls._ParseStringOption(options, 'elastic_user')
    elastic_password = cls._ParseStringOption(options, 'elastic_password')
    use_ssl = getattr(options, 'use_ssl', False)

    ca_certificates_path = cls._ParseStringOption(
        options, 'ca_certificates_file_path')
    elastic_url_prefix = cls._ParseStringOption(options, 'elastic_url_prefix')

    if elastic_password is None:
      elastic_password = os.getenv('PLASO_ELASTIC_PASSWORD', None)

    if elastic_password is not None:
      logger.warning(
          'Note that specifying your Elasticsearch password via '
          '--elastic_password or the environment PLASO_ELASTIC_PASSWORD can '
          'expose the password to other users on the system.')

    if elastic_user is not None and elastic_password is None:
      elastic_password = getpass.getpass('Enter your Elasticsearch password: ')

    ElasticSearchServerArgumentsHelper.ParseOptions(options, output_module)

    output_module.SetIndexName(index_name)
    output_module.SetFlushInterval(flush_interval)
    output_module.SetFields([
        field_name.strip() for field_name in fields.split(',')])

    output_module.SetUsername(elastic_user)
    output_module.SetPassword(elastic_password)
    output_module.SetUseSSL(use_ssl)
    output_module.SetCACertificatesPath(ca_certificates_path)
    output_module.SetURLPrefix(elastic_url_prefix)

    # TODO: remove --raw-field option.
    raw_fields = getattr(options, 'raw_fields', cls._DEFAULT_RAW_FIELDS)
    if raw_fields:
      logger.warning(
          '--raw_fields option is deprecated instead use: '
          '--elastic_mappings=raw_fields.mappings')

    if not mappings_file_path or not os.path.isfile(mappings_file_path):
      mappings_filename = output_module.MAPPINGS_FILENAME
      if raw_fields and isinstance(
          output_module, elastic.ElasticsearchOutputModule):
        mappings_filename = 'raw_fields.mappings'

      mappings_path = getattr(output_module, 'MAPPINGS_PATH', None)
      if mappings_path:
        mappings_file_path = os.path.join(mappings_path, mappings_filename)
      else:
        data_location = getattr(options, '_data_location', None) or 'data'
        mappings_file_path = os.path.join(data_location, mappings_filename)

    if not mappings_file_path or not os.path.isfile(mappings_file_path):
      raise errors.BadConfigOption(
          'No such Elasticsearch mappings file: {0!s}.'.format(
              mappings_file_path))

    with open(mappings_file_path, 'r') as file_object:
      mappings_json = json.load(file_object)

    output_module.SetMappings(mappings_json)


manager.ArgumentHelperManager.RegisterHelper(ElasticSearchOutputArgumentsHelper)
