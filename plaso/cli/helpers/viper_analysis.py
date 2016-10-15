# -*- coding: utf-8 -*-
"""The Viper analysis plugin CLI arguments helper."""

from plaso.analysis import viper
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class ViperAnalysisArgumentsHelper(interface.ArgumentsHelper):
  """Viper analysis plugin CLI arguments helper."""

  NAME = u'viper_analysis'
  CATEGORY = u'analysis'
  DESCRIPTION = u'Argument helper for the Viper analysis plugin.'

  _DEFAULT_HASH = u'sha256'
  _DEFAULT_HOSTNAME = u'localhost'
  _DEFAULT_PORT = 8080
  _DEFAULT_PROTOCOL = u'http'

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
        u'--viper-hash', u'--viper_hash', dest=u'viper_hash', type=str,
        action='store', choices=[u'sha256'], default=cls._DEFAULT_HASH,
        metavar=u'HASH', help=(
            u'Type of hash to query the Viper server, the default is: '
            u'{0:s}'.format(cls._DEFAULT_HASH)))

    argument_group.add_argument(
        u'--viper-host', u'--viper_host', dest=u'viper_host', type=str,
        action='store', default=cls._DEFAULT_HOSTNAME, metavar=u'HOSTNAME',
        help=(
            u'Hostname of the Viper server to query, the default is: '
            u'{0:s}'.format(cls._DEFAULT_HOSTNAME)))

    argument_group.add_argument(
        u'--viper-port', u'--viper_port', dest=u'viper_port', type=int,
        action='store', default=cls._DEFAULT_PORT, metavar=u'PORT', help=(
            u'Port of the Viper server to query, the default is: {0:d}.'.format(
                cls._DEFAULT_PORT)))

    argument_group.add_argument(
        u'--viper-protocol', u'--viper_protocol', dest=u'viper_protocol',
        type=str, choices=[u'http', u'https'], action='store',
        default=cls._DEFAULT_PROTOCOL, metavar=u'PROTOCOL', help=(
            u'Protocol to use to query Viper.'))

  @classmethod
  def ParseOptions(cls, options, analysis_plugin):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      analysis_plugin (ViperAnalysisPlugin): analysis plugin to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
    """
    if not isinstance(analysis_plugin, viper.ViperAnalysisPlugin):
      raise errors.BadConfigObject(
          u'Analysis plugin is not an instance of ViperAnalysisPlugin')

    lookup_hash = cls._ParseStringOption(
        options, u'viper_hash', default_value=cls._DEFAULT_HASH)
    analysis_plugin.SetLookupHash(lookup_hash)

    host = cls._ParseStringOption(
        options, u'viper_host', default_value=cls._DEFAULT_HOSTNAME)
    analysis_plugin.SetHostname(host)

    port = cls._ParseStringOption(
        options, u'viper_port', default_value=cls._DEFAULT_PORT)
    analysis_plugin.SetPort(port)

    protocol = cls._ParseStringOption(
        options, u'viper_protocol', default_value=cls._DEFAULT_PROTOCOL)
    analysis_plugin.SetProtocol(protocol)


manager.ArgumentHelperManager.RegisterHelper(ViperAnalysisArgumentsHelper)
