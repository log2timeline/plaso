# -*- coding: utf-8 -*-
"""The arguments helper for the Elastic Search output module."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.output import elastic


class ElasticOutputHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for an Elastic Search output module."""

  NAME = u'elastic'
  CATEGORY = u'output'
  DESCRIPTION = u'Argument helper for the Elastic Search output module.'

  DEFAULT_ELASTIC_SERVER = u'127.0.0.1'
  DEFAULT_ELASTIC_PORT = 9200

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
    argument_group.add_argument(
        u'--elastic_server_ip', dest=u'elastic_server', type=unicode,
        action=u'store', default=u'127.0.0.1', metavar=u'HOSTNAME', help=(
            u'If the ElasticSearch database resides on a different server '
            u'than localhost this parameter needs to be passed in. This '
            u'should be the IP address or the hostname of the server.'))
    argument_group.add_argument(
        u'--elastic_port', dest=u'elastic_port', type=int, action=u'store',
        default=9200, metavar=u'PORT', help=(
            u'By default ElasticSearch uses the port number 9200, if the '
            u'database is listening on a different port this parameter '
            u'can be defined.'))

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
      raise errors.WrongHelper(u'Only works on Elastic output module.')

    elastic_server = getattr(options, u'elastic_server', None)
    if elastic_server is None:
      raise errors.BadConfigOption(u'Elastic server not set')

    if not elastic_server:
      elastic_server = cls.DEFAULT_ELASTIC_SERVER

    elastic_port = getattr(options, u'elastic_port', None)
    if elastic_port is None:
      raise errors.BadConfigOption(u'Elastic port not set')

    if elastic_port and not isinstance(elastic_port, (int, long)):
      raise errors.BadConfigOption(u'Elastic port needs to be an integer.')

    if not elastic_port:
      elastic_port = cls.DEFAULT_ELASTIC_PORT

    case_name = getattr(options, u'case_name', None)
    document_type = getattr(options, u'document_type', None)

    output_module.SetCaseName(case_name)
    output_module.SetDocumentType(document_type)
    output_module.SetElasticServer(elastic_server, elastic_port)


manager.ArgumentHelperManager.RegisterHelper(ElasticOutputHelper)
