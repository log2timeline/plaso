# -*- coding: utf-8 -*-
"""The Viper analysis plugin CLI arguments helper."""

from __future__ import unicode_literals

from plaso.analysis import viper
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class ViperAnalysisArgumentsHelper(interface.ArgumentsHelper):
  """Viper analysis plugin CLI arguments helper."""

  NAME = 'viper'
  CATEGORY = 'analysis'
  DESCRIPTION = 'Argument helper for the Viper analysis plugin.'

  _DEFAULT_HASH = 'sha256'
  _DEFAULT_HOST = 'localhost'
  _DEFAULT_PORT = 8080
  _DEFAULT_PROTOCOL = 'http'

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
        '--viper-hash', '--viper_hash', dest='viper_hash', type=str,
        action='store', choices=viper.ViperAnalyzer.SUPPORTED_HASHES,
        default=cls._DEFAULT_HASH, metavar='HASH', help=(
            'Type of hash to use to query the Viper server, the default is: '
            '{0:s}. Supported options: {1:s}').format(
                cls._DEFAULT_HASH, ', '.join(
                    viper.ViperAnalyzer.SUPPORTED_HASHES)))

    argument_group.add_argument(
        '--viper-host', '--viper_host', dest='viper_host', type=str,
        action='store', default=cls._DEFAULT_HOST, metavar='HOST',
        help=(
            'Hostname of the Viper server to query, the default is: '
            '{0:s}'.format(cls._DEFAULT_HOST)))

    argument_group.add_argument(
        '--viper-port', '--viper_port', dest='viper_port', type=int,
        action='store', default=cls._DEFAULT_PORT, metavar='PORT', help=(
            'Port of the Viper server to query, the default is: {0:d}.'.format(
                cls._DEFAULT_PORT)))

    argument_group.add_argument(
        '--viper-protocol', '--viper_protocol', dest='viper_protocol',
        type=str, choices=viper.ViperAnalyzer.SUPPORTED_PROTOCOLS,
        action='store', default=cls._DEFAULT_PROTOCOL, metavar='PROTOCOL',
        help=(
            'Protocol to use to query Viper, the default is: {0:s}. '
            'Supported options: {1:s}').format(
                cls._DEFAULT_PROTOCOL, ', '.join(
                    viper.ViperAnalyzer.SUPPORTED_PROTOCOLS)))

  # pylint: disable=arguments-differ
  @classmethod
  # pylint: disable=arguments-differ
  def ParseOptions(cls, options, analysis_plugin):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      analysis_plugin (ViperAnalysisPlugin): analysis plugin to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when unable to connect to Viper instance.
    """
    if not isinstance(analysis_plugin, viper.ViperAnalysisPlugin):
      raise errors.BadConfigObject(
          'Analysis plugin is not an instance of ViperAnalysisPlugin')

    lookup_hash = cls._ParseStringOption(
        options, 'viper_hash', default_value=cls._DEFAULT_HASH)
    analysis_plugin.SetLookupHash(lookup_hash)

    host = cls._ParseStringOption(
        options, 'viper_host', default_value=cls._DEFAULT_HOST)
    analysis_plugin.SetHost(host)

    port = cls._ParseNumericOption(
        options, 'viper_port', default_value=cls._DEFAULT_PORT)
    analysis_plugin.SetPort(port)

    protocol = cls._ParseStringOption(
        options, 'viper_protocol', default_value=cls._DEFAULT_PROTOCOL)
    protocol = protocol.lower().strip()
    analysis_plugin.SetProtocol(protocol)

    if not analysis_plugin.TestConnection():
      raise errors.BadConfigOption(
          'Unable to connect to Viper {0:s}:{1:d}'.format(host, port))


manager.ArgumentHelperManager.RegisterHelper(ViperAnalysisArgumentsHelper)
