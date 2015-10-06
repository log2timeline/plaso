# -*- coding: utf-8 -*-
"""The arguments helper for the Viper analysis plugin."""

from plaso.analysis import viper
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class ViperAnalysisHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for the Viper analysis plugin."""

  NAME = u'viper_analysis'
  CATEGORY = u'analysis'
  DESCRIPTION = u'Argument helper for the Viper analysis plugin.'

  _DEFAULT_HOST = u'localhost:8080'
  _DEFAULT_PROTOCOL = u'http'

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
        u'--viper-host', dest=u'viper_host',
        type=str, action='store', default=cls._DEFAULT_HOST,
        help=u'Specify the host to query Viper on.')
    argument_group.add_argument(
        u'--viper-protocol', dest=u'viper_protocol', type=str,
        choices=[u'http', u'https'], action='store',
        default=cls._DEFAULT_PROTOCOL,
        help=u'Protocol to use to query Viper.')

  @classmethod
  def ParseOptions(cls, options, analysis_plugin):
    """Parses and validates options.

    Args:
      options: the parser option object (instance of argparse.Namespace).
      analysis_plugin: an analysis plugin (instance of AnalysisPlugin).

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
    """
    if not isinstance(analysis_plugin, viper.ViperAnalysisPlugin):
      raise errors.BadConfigObject(
          u'Analysis plugin is not an instance of ViperAnalysisPlugin')

    host = cls._ParseStringOption(
        options, u'viper_host', default_value=cls._DEFAULT_HOST)
    analysis_plugin.SetHost(host)

    protocol = cls._ParseStringOption(
        options, u'viper_protocol', default_value=cls._DEFAULT_PROTOCOL)
    analysis_plugin.SetProtocol(protocol)


manager.ArgumentHelperManager.RegisterHelper(ViperAnalysisHelper)
