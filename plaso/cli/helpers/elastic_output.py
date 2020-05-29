# -*- coding: utf-8 -*-
"""The Elastic Search output module CLI arguments helper."""

from __future__ import unicode_literals

import getpass
import os

from uuid import uuid4

from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.cli.helpers import server_config
from plaso.cli import logger
from plaso.lib import errors
from plaso.output import elastic


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
  _DEFAULT_DOCUMENT_TYPE = 'plaso_event'
  _DEFAULT_FLUSH_INTERVAL = 1000
  _DEFAULT_RAW_FIELDS = False

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
        '--index_name', dest='index_name', type=str, action='store',
        default=cls._DEFAULT_INDEX_NAME, help=(
            'Name of the index in ElasticSearch.'))
    argument_group.add_argument(
        '--doc_type', dest='document_type', type=str,
        action='store', default=cls._DEFAULT_DOCUMENT_TYPE, help=(
            'Name of the document type that will be used in ElasticSearch.'))
    argument_group.add_argument(
        '--flush_interval', dest='flush_interval', type=int,
        action='store', default=cls._DEFAULT_FLUSH_INTERVAL, help=(
            'Events to queue up before bulk insert to ElasticSearch.'))
    argument_group.add_argument(
        '--raw_fields', dest='raw_fields', action='store_true',
        default=cls._DEFAULT_RAW_FIELDS, help=(
            'Export string fields that will not be analyzed by Lucene.'))
    argument_group.add_argument(
        '--elastic_user', dest='elastic_user', action='store',
        default=None, help='Username to use for Elasticsearch authentication.')
    argument_group.add_argument(
        '--elastic_password', dest='elastic_password', action='store',
        default=None, help=(
            'Password to use for Elasticsearch authentication. WARNING: use '
            'with caution since this can expose the password to other users '
            'on the system. The password can also be set with the environment '
            'variable PLASO_ELASTIC_PASSWORD. '))
    argument_group.add_argument(
        '--use_ssl', dest='use_ssl', action='store_true',
        help='Enforces use of ssl.')
    argument_group.add_argument(
        '--ca_certificates_file_path', dest='ca_certificates_file_path',
        action='store', type=str, default=None, help=(
            'Path to a file containing a list of root certificates to trust.'))
    argument_group.add_argument(
        '--elastic_url_prefix', dest='elastic_url_prefix', type=str,
        action='store', default=None, help='URL prefix for elastic search.')

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
    elastic_output_modules = (
        elastic.ElasticsearchOutputModule, elastic.ElasticsearchOutputModule)
    if not isinstance(output_module, elastic_output_modules):
      raise errors.BadConfigObject(
          'Output module is not an instance of ElasticsearchOutputModule')

    index_name = cls._ParseStringOption(
        options, 'index_name', default_value=cls._DEFAULT_INDEX_NAME)
    document_type = cls._ParseStringOption(
        options, 'document_type', default_value=cls._DEFAULT_DOCUMENT_TYPE)
    flush_interval = cls._ParseNumericOption(
        options, 'flush_interval', default_value=cls._DEFAULT_FLUSH_INTERVAL)
    raw_fields = getattr(options, 'raw_fields', cls._DEFAULT_RAW_FIELDS)
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
    output_module.SetDocumentType(document_type)
    output_module.SetFlushInterval(flush_interval)
    output_module.SetRawFields(raw_fields)
    output_module.SetUsername(elastic_user)
    output_module.SetPassword(elastic_password)
    output_module.SetUseSSL(use_ssl)
    output_module.SetCACertificatesPath(ca_certificates_path)
    output_module.SetURLPrefix(elastic_url_prefix)


manager.ArgumentHelperManager.RegisterHelper(ElasticSearchOutputArgumentsHelper)
