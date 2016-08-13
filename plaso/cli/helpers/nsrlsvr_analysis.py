# -*- coding: utf-8 -*-
"""Arguments helper for the nsrlsvr analysis plugin."""

from plaso.analysis import nsrlsvr
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class NsrlsvrAnalysisHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for the nsrlsvr analysis plugin."""

  NAME = u'nsrlsvr_analysis'
  CATEGORY = u'analysis'
  DESCRIPTION = u'Argument helper for the nsrlsvr analysis plugin.'

  _DEFAULT_HOST = u'localhost'
  _DEFAULT_PORT = 9120

  @classmethod
  def AddArguments(cls, argument_group):
    """Add command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser): group
          to append arguments to.
    """
    argument_group.add_argument(
        u'--nsrlsvr-host', dest=u'nsrlsvr_host', type=str, action='store',
        default=cls._DEFAULT_HOST,
        help=u'Specify the host to query Nsrlsvr on.')
    argument_group.add_argument(
        u'--nsrlsvr-port', dest=u'nsrlvr_port', type=int, action='store',
        default=cls._DEFAULT_PORT,
        help=u'Port to use to query Nsrlsvr.')

  @classmethod
  def ParseOptions(cls, options, analysis_plugin):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options object.
      analysis_plugin (AnalysisPlugin): analysis plugin to configure.

    Raises:
      BadConfigObject: when the analysis plugin is the wrong type.
    """
    if not isinstance(analysis_plugin, nsrlsvr.NsrlsvrAnalysisPlugin):
      raise errors.BadConfigObject(
          u'Analysis plugin is not an instance of NsrlsvrAnalysisPlugin')

    host = cls._ParseStringOption(
        options, u'nsrlsvr_host', default_value=cls._DEFAULT_HOST)
    analysis_plugin.SetHost(host)

    port = cls._ParseStringOption(
        options, u'nsrlsvr_port', default_value=cls._DEFAULT_PORT)
    analysis_plugin.SetPort(port)


manager.ArgumentHelperManager.RegisterHelper(NsrlsvrAnalysisHelper)
