# -*- coding: utf-8 -*-
"""The arguments helper for the Elastic Search output module."""

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
        u'--case_name', dest=u'case_name', type=unicode, action=u'store',
        default=u'', help=(
            u'Add a case name. This will be the name of the index in '
            u'ElasticSearch.'))
    argument_group.add_argument(
        u'--document_type', dest=u'document_type', type=unicode,
        action=u'store', default=u'', help=(
            u'Name of the document type. This is the name of the document '
            u'type that will be used in ElasticSearch.'))

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
    if output_format != u'elastic':
      raise errors.BadConfigOption(u'Only works on Elastic output module.')

    case_name = getattr(options, u'case_name', None)
    document_type = getattr(options, u'document_type', None)

    ElasticServer.ParseOptions(options, output_module)
    output_module.SetCaseName(case_name)
    output_module.SetDocumentType(document_type)


manager.ArgumentHelperManager.RegisterHelper(ElasticOutputHelper)
