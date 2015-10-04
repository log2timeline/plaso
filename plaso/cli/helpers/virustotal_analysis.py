# -*- coding: utf-8 -*-
"""The arguments helper for the VirusTotal analysis plugin."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.analysis import virustotal


class VirusTotalAnalysisHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for the VirusTotal analysis plugin."""

  NAME = u'virustotal_analysis'
  CATEGORY = u'analysis'
  DESCRIPTION = u'Argument helper for the VirusTotal analysis plugin.'

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
        u'--virustotal-api-key', dest=u'virustotal_api_key',
        type=str, action='store', default=None, help=u'Specify the API key '
        u'for use with VirusTotal.')
    argument_group.add_argument(
        u'--virustotal-free-rate-limit', dest=u'virustotal_rate_limit',
        type=bool, action='store', default=True, help=u'Limit Virustotal '
        u'requests to the default free API key rate of 4 requests per minute. '
        u'Set this to false if you have an key for the private API.')

  @classmethod
  def ParseOptions(cls, options, analysis_plugin):
    """Parses and validates options.

    Args:
      options: the parser option object (instance of argparse.Namespace).
      analysis_plugin: an analysis plugin (instance of AnalysisPlugin).

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not isinstance(analysis_plugin, virustotal.VirusTotalAnalysisPlugin):
      raise errors.BadConfigObject(
          u'Analysis plugin is not an instance of VirusTotalAnalysisPlugin')

    api_key = cls._ParseStringOption(options, u'virustotal_api_key')
    if not api_key:
      raise errors.BadConfigOption(
          u'VirusTotal API key not specified. Try again with '
          u'--virustotal-api-key.')

    rate_limit = getattr(options, u'virustotal_rate_limit', None)

    analysis_plugin.SetAPIKey(api_key)
    analysis_plugin.EnableFreeAPIKeyRateLimit(rate_limit)


manager.ArgumentHelperManager.RegisterHelper(VirusTotalAnalysisHelper)
