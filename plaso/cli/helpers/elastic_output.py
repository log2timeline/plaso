# -*- coding: utf-8 -*-
"""The arguments helper for the Elastic Search output module."""

from uuid import uuid4

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.cli.helpers import server_config
from plaso.output import elastic


class ElasticServer(server_config.BaseServerConfigHelper):
  """CLI argument helper for an Elastic Search server."""

  _DEFAULT_SERVER = u'127.0.0.1'
  _DEFAULT_PORT = 9200


class ElasticOutputHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for an Elastic Search output module."""

  NAME = u'elastic'
  CATEGORY = u'output'
  DESCRIPTION = u'Argument helper for the Elastic Search output module.'

  _DEFAULT_INDEX_NAME = uuid4().hex
  _DEFAULT_DOC_TYPE = u'plaso_event'
  _DEFAULT_FLUSH_INTERVAL = 1000

  @classmethod
  def AddArguments(cls, argument_group):
    """Add command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group: the argparse group (instance of argparse._ArgumentGroup or
                      or argparse.ArgumentParser).
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

    ElasticServer.AddArguments(argument_group)

  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options: the parser option object (instance of argparse.Namespace).
      output_module: an output module (instance of OutputModule).

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not isinstance(output_module, elastic.ElasticSearchOutputModule):
      raise errors.BadConfigObject(
          u'Output module is not an instance of ElasticSearchOutputModule')

    output_format = getattr(options, u'output_format', None)
    if output_format not in [u'elastic', u'timesketch']:
      raise errors.BadConfigOption(
          u'Only works on Elastic or Timesketch output module.')

    index_name = cls._ParseStringOption(
        options, u'index_name', default_value=cls._DEFAULT_INDEX_NAME)
    doc_type = cls._ParseStringOption(
        options, u'doc_type', default_value=cls._DEFAULT_DOC_TYPE)
    flush_interval = cls._ParseIntegerOption(
        options, u'flush_interval', default_value=cls._DEFAULT_FLUSH_INTERVAL)

    ElasticServer.ParseOptions(options, output_module)
    output_module.SetIndexName(index_name)
    output_module.SetDocType(doc_type)
    output_module.SetFlushInterval(flush_interval)


manager.ArgumentHelperManager.RegisterHelper(ElasticOutputHelper)
