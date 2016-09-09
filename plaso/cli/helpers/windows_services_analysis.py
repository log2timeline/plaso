# -*- coding: utf-8 -*-
"""The Windows Services analysis plugin CLI arguments helper."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.analysis import windows_services


class WindowsServicesAnalysisArgumentsHelper(interface.ArgumentsHelper):
  """Windows Services analysis plugin CLI arguments helper."""

  NAME = u'windows_services'
  CATEGORY = u'analysis'
  DESCRIPTION = u'Argument helper for the Windows Services analysis plugin.'

  _DEFAULT_OUTPUT = u'text'

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
        u'--windows-services-output', dest=u'windows_services_output',
        type=str, action=u'store', default=cls._DEFAULT_OUTPUT,
        choices=[u'text', u'yaml'], help=(
            u'Specify how the results should be displayed. Options are text '
            u'and yaml.'))

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
          u'Analysis plugin is not an instance of '
          u'WindowsServicesAnalysisPlugin'))

    output_format = cls._ParseStringOption(
        options, u'windows_services_output', default_value=cls._DEFAULT_OUTPUT)
    analysis_plugin.SetOutputFormat(output_format)


manager.ArgumentHelperManager.RegisterHelper(
    WindowsServicesAnalysisArgumentsHelper)
