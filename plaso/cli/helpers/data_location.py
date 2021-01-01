# -*- coding: utf-8 -*-
"""The data location CLI arguments helper."""

import os
import sys

from plaso.cli import tools
from plaso.cli import logger
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class DataLocationArgumentsHelper(interface.ArgumentsHelper):
  """Data location CLI arguments helper."""

  NAME = 'data_location'
  DESCRIPTION = 'Data location command line arguments.'

  # Preserve the absolute path value of __file__ in case it is changed
  # at run-time.
  _PATH = os.path.abspath(__file__)

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
        '--data', action='store', dest='data_location', type=str,
        metavar='PATH', default=None, help=(
            'Path to a directory containing the data files.'))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: when the location of the data files cannot be determined.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    data_location = cls._ParseStringOption(options, 'data_location')
    if not data_location:
      # Determine the source root path, which is 3 directories up from
      # the location of the script.
      data_location = os.path.dirname(cls._PATH)
      data_location = os.path.dirname(data_location)
      data_location = os.path.dirname(data_location)
      data_location = os.path.dirname(data_location)

      # There are multiple options to run a tool e.g. running from source or
      # from an egg file.
      data_location_egg = os.path.join(data_location, 'share', 'plaso')
      data_location_source = os.path.join(data_location, 'data')

      data_location = None
      if os.path.exists(data_location_egg) and os.path.isfile(os.path.join(
          data_location_egg, 'plaso-data.README')):
        data_location = data_location_egg
      elif os.path.exists(data_location_source) and os.path.isfile(os.path.join(
          data_location_source, 'plaso-data.README')):
        data_location = data_location_source

      if not data_location or not os.path.exists(data_location):
        data_location = os.path.join(sys.prefix, 'share', 'plaso')
      if not os.path.exists(data_location):
        data_location = os.path.join(sys.prefix, 'local', 'share', 'plaso')

      if sys.prefix != '/usr':
        if not os.path.exists(data_location):
          data_location = os.path.join('/usr', 'share', 'plaso')
        if not os.path.exists(data_location):
          data_location = os.path.join('/usr', 'local', 'share', 'plaso')

      if not os.path.exists(data_location) or not os.path.isfile(os.path.join(
          data_location, 'plaso-data.README')):
        data_location = None

    if not data_location:
      raise errors.BadConfigOption(
          'Unable to determine location of data files.')

    logger.info('Determined data location: {0:s}'.format(data_location))

    setattr(configuration_object, '_data_location', data_location)


manager.ArgumentHelperManager.RegisterHelper(DataLocationArgumentsHelper)
