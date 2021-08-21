# -*- coding: utf-8 -*-
"""The VirusTotal analysis plugin CLI arguments helper."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.analysis import virustotal


class VirusTotalAnalysisArgumentsHelper(interface.ArgumentsHelper):
  """VirusTotal analysis plugin CLI arguments helper."""

  NAME = 'virustotal'
  CATEGORY = 'analysis'
  DESCRIPTION = 'Argument helper for the VirusTotal analysis plugin.'

  _DEFAULT_HASH = 'sha256'
  _DEFAULT_RATE_LIMIT = True

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
        '--virustotal-api-key', '--virustotal_api_key',
        dest='virustotal_api_key', type=str, action='store', default=None,
        metavar='API_KEY', help=(
            'Specify the API key for use with VirusTotal.'))

    argument_group.add_argument(
        '--virustotal-free-rate-limit', '--virustotal_free_rate_limit',
        dest='virustotal_free_rate_limit',
        action='store_false', default=cls._DEFAULT_RATE_LIMIT, help=(
            'Limit Virustotal requests to the default free API key rate of '
            '4 requests per minute. Set this to false if you have an key '
            'for the private API.'))

    argument_group.add_argument(
        '--virustotal-hash', '--virustotal_hash', dest='virustotal_hash',
        type=str, action='store', choices=['md5', 'sha1', 'sha256'],
        default=cls._DEFAULT_HASH, metavar='HASH', help=(
            'Type of hash to query VirusTotal, the default is: {0:s}'.format(
                cls._DEFAULT_HASH)))

  @classmethod
  def ParseOptions(cls, options, analysis_plugin):  # pylint: disable=arguments-renamed
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      analysis_plugin (VirusTotalAnalysisPlugin): analysis plugin to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation or
          when unable to connect to VirusTotal.
    """
    if not isinstance(analysis_plugin, virustotal.VirusTotalAnalysisPlugin):
      raise errors.BadConfigObject(
          'Analysis plugin is not an instance of VirusTotalAnalysisPlugin')

    api_key = cls._ParseStringOption(options, 'virustotal_api_key')
    if not api_key:
      raise errors.BadConfigOption(
          'VirusTotal API key not specified. Try again with '
          '--virustotal-api-key.')

    analysis_plugin.SetAPIKey(api_key)

    enable_rate_limit = getattr(
        options, 'virustotal_free_rate_limit', cls._DEFAULT_RATE_LIMIT)
    if enable_rate_limit:
      analysis_plugin.EnableFreeAPIKeyRateLimit()

    lookup_hash = cls._ParseStringOption(
        options, 'virustotal_hash', default_value=cls._DEFAULT_HASH)
    analysis_plugin.SetLookupHash(lookup_hash)

    if not analysis_plugin.TestConnection():
      raise errors.BadConfigOption('Unable to connect to VirusTotal')


manager.ArgumentHelperManager.RegisterHelper(VirusTotalAnalysisArgumentsHelper)
