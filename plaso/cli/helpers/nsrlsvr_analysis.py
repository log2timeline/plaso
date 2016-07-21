# -*- coding: utf-8 -*-
"""The arguments helper for the Nsrlsvr analysis plugin."""

from plaso.analysis import nsrlsvr
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class NsrlsvrAnalysisHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for the Nsrlsvr analysis plugin."""

  NAME = u'nsrlsvr_analysis'
  CATEGORY = u'analysis'
  DESCRIPTION = u'Argument helper for the Nsrlsvr analysis plugin.'

  _DEFAULT_HOST = u'localhost'
  _DEFAULT_PORT = u'9120'

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
        u'--nsrlsvr-host', dest=u'nsrlsvr_host',
        type=str, action='store', default=cls._DEFAULT_HOST,
        help=u'Specify the host to query Nsrlsvr on.')
    argument_group.add_argument(
        u'--nsrlsvr-port', dest=u'nsrlvr_port', type=str,
        action='store', default=cls._DEFAULT_PORT,
        help=u'Port to use to query Nsrlsvr.')

  @classmethod
  def ParseOptions(cls, options, analysis_plugin):
    """Parses and validates options.

    Args:
      options: the parser option object (instance of argparse.Namespace).
      analysis_plugin: an analysis plugin (instance of AnalysisPlugin).

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
    """
    if not isinstance(analysis_plugin, nsrlsvr.NsrlsvrAnalysisPlugin):
      raise errors.BadConfigObject(
          u'Analysis plugin is not an instance of NsrlsvrAnalysisPlugin')

    host = cls._ParseStringOption(
        options, u'nsrlsvr_host', default_value=cls._DEFAULT_HOST)
    analysis_plugin.SetHost(host)

    protocol = cls._ParseStringOption(
        options, u'nsrlsvr_protocol', default_value=cls._DEFAULT_PORT)
    analysis_plugin.SetPort(protocol)


manager.ArgumentHelperManager.RegisterHelper(NsrlsvrAnalysisHelper)
