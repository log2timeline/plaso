# -*- coding: utf-8 -*-
"""The filter file CLI arguments helper."""

import os

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class FilterFileArgumentsHelper(interface.ArgumentsHelper):
  """Filter file CLI arguments helper."""

  NAME = 'filter_file'
  DESCRIPTION = 'Filter file command line arguments.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    argument_group.add_argument(
        '-f', '--filter-file', '--filter_file', '--file-filter',
        '--file_filter', dest='file_filter', action='store', type=str,
        default=None, help=(
            'List of files to include for targeted collection of files to '
            'parse, one line per file path, setup is /path|file - where each '
            'element can contain either a variable set in the preprocessing '
            'stage or a regular expression.'))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: if the collection file does not exist.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    filter_file = cls._ParseStringOption(options, 'file_filter')

    # Search the data location for the filter file.
    if filter_file and not os.path.isfile(filter_file):
      if configuration_object.data_location:
        filter_file_basename = os.path.basename(filter_file)
        filter_file_path = os.path.join(
            configuration_object.data_location, filter_file_basename)
        if os.path.isfile(filter_file_path):
          filter_file = filter_file_path

    if filter_file and not os.path.isfile(filter_file):
      raise errors.BadConfigOption(
          'No such collection filter file: {0:s}.'.format(filter_file))

    setattr(configuration_object, '_filter_file', filter_file)


manager.ArgumentHelperManager.RegisterHelper(FilterFileArgumentsHelper)
