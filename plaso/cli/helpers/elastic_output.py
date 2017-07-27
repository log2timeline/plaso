# -*- coding: utf-8 -*-
"""The Elastic Search output module CLI arguments helper."""

from uuid import uuid4
import getpass

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.cli.helpers import server_config
from plaso.output import elastic


class ElasticSearchServerArgumentsHelper(server_config.ServerArgumentsHelper):
  """Elastic Search server CLI arguments helper."""

  _DEFAULT_SERVER = u'127.0.0.1'
  _DEFAULT_PORT = 9200


class ElasticSearchOutputArgumentsHelper(interface.ArgumentsHelper):
  """Elastic Search output module CLI arguments helper."""

  NAME = u'elastic'
  CATEGORY = u'output'
  DESCRIPTION = u'Argument helper for the Elastic Search output module.'

  _DEFAULT_INDEX_NAME = uuid4().hex
  _DEFAULT_DOC_TYPE = u'plaso_event'
  _DEFAULT_FLUSH_INTERVAL = 1000
  _DEFAULT_RAW_FIELDS = False
  _DEFAULT_ELASTIC_USER = None

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
        u'--index_name', dest=u'index_name', type=str, action=u'store',
        default=cls._DEFAULT_INDEX_NAME, help=(
            u'Name of the index in ElasticSearch.'))
    argument_group.add_argument(
        u'--doc_type', dest=u'doc_type', type=str,
        action=u'store', default=cls._DEFAULT_DOC_TYPE, help=(
            u'Name of the document type that will be used in ElasticSearch.'))
    argument_group.add_argument(
        u'--flush_interval', dest=u'flush_interval', type=int,
        action=u'store', default=cls._DEFAULT_FLUSH_INTERVAL, help=(
            u'Events to queue up before bulk insert to ElasticSearch.'))
    argument_group.add_argument(
        u'--raw_fields', dest=u'raw_fields', action=u'store_true',
        default=cls._DEFAULT_RAW_FIELDS, help=(
            u'Export string fields that will not be analyzed by Lucene.'))
    argument_group.add_argument(
        u'--elastic_user', dest=u'elastic_user', action=u'store',
        default=cls._DEFAULT_ELASTIC_USER, help=(
            u'Username to use for Elasticsearch authentication.'))

    ElasticSearchServerArgumentsHelper.AddArguments(argument_group)

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
    if not isinstance(output_module, elastic.ElasticSearchOutputModule):
      raise errors.BadConfigObject(
          u'Output module is not an instance of ElasticSearchOutputModule')

    index_name = cls._ParseStringOption(
        options, u'index_name', default_value=cls._DEFAULT_INDEX_NAME)
    doc_type = cls._ParseStringOption(
        options, u'doc_type', default_value=cls._DEFAULT_DOC_TYPE)
    flush_interval = cls._ParseNumericOption(
        options, u'flush_interval', default_value=cls._DEFAULT_FLUSH_INTERVAL)
    raw_fields = getattr(
        options, u'raw_fields', cls._DEFAULT_RAW_FIELDS)
    elastic_user = cls._ParseStringOption(
        options, u'elastic_user', default_value=cls._DEFAULT_ELASTIC_USER)

    if elastic_user is not None:
      elastic_password = getpass.getpass(
          u'Enter your Elasticsearch password: ')
    else:
      elastic_password = None

    ElasticSearchServerArgumentsHelper.ParseOptions(options, output_module)
    output_module.SetIndexName(index_name)
    output_module.SetDocType(doc_type)
    output_module.SetFlushInterval(flush_interval)
    output_module.SetRawFields(raw_fields)
    output_module.SetElasticUser(elastic_user)
    output_module.SetElasticPassword(elastic_password)


manager.ArgumentHelperManager.RegisterHelper(ElasticSearchOutputArgumentsHelper)
