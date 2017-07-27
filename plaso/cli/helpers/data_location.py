# -*- coding: utf-8 -*-
"""The data location CLI arguments helper."""

import os
import sys

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class DataLocationArgumentsHelper(interface.ArgumentsHelper):
  """Data location CLI arguments helper."""

  NAME = u'data_location'
  DESCRIPTION = u'Data location command line arguments.'

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
        u'--data', action=u'store', dest=u'data_location', type=str,
        metavar=u'PATH', default=None, help=u'the location of the data files.')

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          u'Configuration object is not an instance of CLITool')

    data_location = cls._ParseStringOption(options, u'data_location')
    if not data_location:
      # Determine the source root path, which is 3 directories up from
      # the location of the script.
      data_location = os.path.dirname(cls._PATH)
      data_location = os.path.dirname(data_location)
      data_location = os.path.dirname(data_location)
      data_location = os.path.dirname(data_location)

      # There are multiple options to run a tool e.g. running from source or
      # from an egg file.
      data_location_egg = os.path.join(data_location, u'share', u'plaso')
      data_location_source = os.path.join(data_location, u'data')
      data_location_system = os.path.join(sys.prefix, u'share', u'plaso')
      data_location_system_local = os.path.join(
          sys.prefix, u'local', u'share', u'plaso')

      if os.path.exists(data_location_egg):
        data_location = data_location_egg
      elif os.path.exists(data_location_source):
        data_location = data_location_source
      elif os.path.exists(data_location_system):
        data_location = data_location_system
      elif os.path.exists(data_location_system_local):
        data_location = data_location_system_local
      else:
        data_location = None

    if not data_location:
      raise errors.BadConfigOption(
          u'Unable to determine location of data files.')

    setattr(configuration_object, u'_data_location', data_location)


manager.ArgumentHelperManager.RegisterHelper(DataLocationArgumentsHelper)
