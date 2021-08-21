# -*- coding: utf-8 -*-
"""The tagging analysis plugin CLI arguments helper."""

import os

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.analysis import tagging


class TaggingAnalysisArgumentsHelper(interface.ArgumentsHelper):
  """Tagging analysis plugin CLI arguments helper."""

  NAME = 'tagging'
  CATEGORY = 'analysis'
  DESCRIPTION = 'Argument helper for the Tagging analysis plugin.'

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
        '--tagging-file', '--tagging_file', dest='tagging_file', type=str,
        help='Specify a file to read tagging criteria from.', action='store')

  @classmethod
  def ParseOptions(cls, options, analysis_plugin):  # pylint: disable=arguments-renamed
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      analysis_plugin (AnalysisPlugin): analysis plugin to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not isinstance(analysis_plugin, tagging.TaggingAnalysisPlugin):
      raise errors.BadConfigObject(
          'Analysis plugin is not an instance of TaggingAnalysisPlugin')

    tagging_file = cls._ParseStringOption(options, 'tagging_file')
    if not tagging_file:
      raise errors.BadConfigOption(
          'Tagging analysis plugin requires a tagging file.')

    tagging_file_path = tagging_file
    if not os.path.isfile(tagging_file_path):
      # Check if the file exists in the data location path.
      data_location = getattr(options, 'data_location', None)
      if data_location:
        tagging_file_path = os.path.join(data_location, tagging_file)

    if not os.path.isfile(tagging_file_path):
      raise errors.BadConfigOption(
          'No such tagging file: {0:s}.'.format(tagging_file))

    try:
      analysis_plugin.SetAndLoadTagFile(tagging_file_path)

    except UnicodeDecodeError:
      raise errors.BadConfigOption(
          'Invalid tagging file: {0:s} encoding must be UTF-8.'.format(
              tagging_file))

    except errors.TaggingFileError as exception:
      raise errors.BadConfigOption(
          'Unable to read tagging file: {0:s} with error: {1!s}'.format(
              tagging_file, exception))


manager.ArgumentHelperManager.RegisterHelper(TaggingAnalysisArgumentsHelper)
