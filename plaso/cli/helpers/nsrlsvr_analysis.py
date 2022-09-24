# -*- coding: utf-8 -*-
"""The nsrlsvr analysis plugin CLI arguments helper."""

from plaso.analysis import nsrlsvr
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class NsrlsvrAnalysisArgumentsHelper(interface.ArgumentsHelper):
  """Nsrlsvr analysis plugin CLI arguments helper."""

  NAME = 'nsrlsvr'
  CATEGORY = 'analysis'
  DESCRIPTION = 'Argument helper for the nsrlsvr analysis plugin.'

  _DEFAULT_HASH = 'md5'
  _DEFAULT_HOST = 'localhost'
  _DEFAULT_LABEL = nsrlsvr.NsrlsvrAnalysisPlugin.DEFAULT_LABEL
  _DEFAULT_PORT = 9120
  _SUPPORTED_HASHES = sorted(nsrlsvr.NsrlsvrAnalysisPlugin.SUPPORTED_HASHES)

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser): group
          to append arguments to.
    """
    argument_group.add_argument(
        '--nsrlsvr-hash', '--nsrlsvr_hash', dest='nsrlsvr_hash', type=str,
        action='store', choices=cls._SUPPORTED_HASHES,
        default=cls._DEFAULT_HASH, metavar='HASH', help=(
            'Type of hash to use to query nsrlsvr instance, the default is: '
            '{0:s}. Supported options: {1:s}'.format(
                cls._DEFAULT_HASH, ', '.join(cls._SUPPORTED_HASHES))))

    argument_group.add_argument(
        '--nsrlsvr-host', '--nsrlsvr_host', dest='nsrlsvr_host', type=str,
        action='store', default=cls._DEFAULT_HOST, metavar='HOST',
        help=(
            'Hostname or IP address of the nsrlsvr instance to query, the '
            'default is: {0:s}').format(cls._DEFAULT_HOST))

    argument_group.add_argument(
        '--nsrlsvr-label', '--nsrlsvr_label', dest='nsrlsvr_label', type=str,
        action='store', default=cls._DEFAULT_LABEL, metavar='LABEL', help=(
            'Label to apply to events, the default is: {0:s}.').format(
                cls._DEFAULT_LABEL))

    argument_group.add_argument(
        '--nsrlsvr-port', '--nsrlsvr_port', dest='nsrlsvr_port', type=int,
        action='store', default=cls._DEFAULT_PORT, metavar='PORT', help=(
            'Port number of the nsrlsvr instance to query, the default is: '
            '{0:d}.').format(cls._DEFAULT_PORT))

  @classmethod
  def ParseOptions(cls, options, analysis_plugin):  # pylint: disable=arguments-renamed
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options object.
      analysis_plugin (NsrlsvrAnalysisPlugin): analysis plugin to configure.

    Raises:
      BadConfigObject: when the analysis plugin is the wrong type.
      BadConfigOption: when unable to connect to nsrlsvr instance.
    """
    if not isinstance(analysis_plugin, nsrlsvr.NsrlsvrAnalysisPlugin):
      raise errors.BadConfigObject(
          'Analysis plugin is not an instance of NsrlsvrAnalysisPlugin')

    label = cls._ParseStringOption(
        options, 'nsrlsvr_label', default_value=cls._DEFAULT_LABEL)
    analysis_plugin.SetLabel(label)

    lookup_hash = cls._ParseStringOption(
        options, 'nsrlsvr_hash', default_value=cls._DEFAULT_HASH)
    analysis_plugin.SetLookupHash(lookup_hash)

    host = cls._ParseStringOption(
        options, 'nsrlsvr_host', default_value=cls._DEFAULT_HOST)
    analysis_plugin.SetHost(host)

    port = cls._ParseNumericOption(
        options, 'nsrlsvr_port', default_value=cls._DEFAULT_PORT)
    analysis_plugin.SetPort(port)

    if not analysis_plugin.TestConnection():
      raise errors.BadConfigOption(
          'Unable to connect to nsrlsvr {0:s}:{1:d}'.format(host, port))


manager.ArgumentHelperManager.RegisterHelper(NsrlsvrAnalysisArgumentsHelper)
