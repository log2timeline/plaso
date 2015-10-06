# -*- coding: utf-8 -*-
"""The arguments helper for the Windows Services analysis plugin."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.analysis import windows_services


class WindowsServicesAnalysisHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for the WindowsServices analysis plugin."""

  NAME = u'windows_services'
  CATEGORY = u'analysis'
  DESCRIPTION = u'Argument helper for the Windows Services analysis plugin.'

  _DEFAULT_OUTPUT = u'text'

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
        u'--windows-services-output', dest=u'windows_services_output',
        type=str, action=u'store', default=cls._DEFAULT_OUTPUT,
        choices=[u'text', u'yaml'], help=(
            u'Specify how the results should be displayed. Options are text '
            u'and yaml.'))

  @classmethod
  def ParseOptions(cls, options, analysis_plugin):
    """Parses and validates options.

    Args:
      options: the parser option object (instance of argparse.Namespace).
      analysis_plugin: an analysis plugin (instance of AnalysisPlugin).

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
    """
    if not isinstance(analysis_plugin, windows_services.WindowsServicesPlugin):
      raise errors.BadConfigObject(
          u'Analysis plugin is not an instance of WindowsServicesPlugin')

    output_format = cls._ParseStringOption(
        options, u'windows_services_output', default_value=cls._DEFAULT_OUTPUT)
    analysis_plugin.SetOutputFormat(output_format)


manager.ArgumentHelperManager.RegisterHelper(WindowsServicesAnalysisHelper)
