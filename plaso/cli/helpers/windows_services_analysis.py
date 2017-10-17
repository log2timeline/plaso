# -*- coding: utf-8 -*-
"""The Windows Services analysis plugin CLI arguments helper."""

from __future__ import unicode_literals

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.analysis import windows_services


class WindowsServicesAnalysisArgumentsHelper(interface.ArgumentsHelper):
  """Windows Services analysis plugin CLI arguments helper."""

  NAME = 'windows_services'
  CATEGORY = 'analysis'
  DESCRIPTION = 'Argument helper for the Windows Services analysis plugin.'

  _DEFAULT_OUTPUT = 'text'

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
        '--windows-services-output', dest='windows_services_output',
        type=str, action='store', default=cls._DEFAULT_OUTPUT,
        choices=['text', 'yaml'], help=(
            'Specify how the results should be displayed. Options are text '
            'and yaml.'))

  # pylint: disable=arguments-differ
  @classmethod
  def ParseOptions(cls, options, analysis_plugin):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      analysis_plugin (WindowsServicePlugin): analysis plugin to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
    """
    if not isinstance(
        analysis_plugin, windows_services.WindowsServicesAnalysisPlugin):
      raise errors.BadConfigObject((
          'Analysis plugin is not an instance of '
          'WindowsServicesAnalysisPlugin'))

    output_format = cls._ParseStringOption(
        options, 'windows_services_output', default_value=cls._DEFAULT_OUTPUT)
    analysis_plugin.SetOutputFormat(output_format)


manager.ArgumentHelperManager.RegisterHelper(
    WindowsServicesAnalysisArgumentsHelper)
