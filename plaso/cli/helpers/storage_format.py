# -*- coding: utf-8 -*-
"""The storage format CLI arguments helper."""

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import definitions
from plaso.lib import errors


class StorageFormatArgumentsHelper(interface.ArgumentsHelper):
  """Storage format CLI arguments helper."""

  NAME = u'storage_format'
  DESCRIPTION = u'Storage format command line arguments.'

  _DEFAULT_STORAGE_FORMAT = definitions.STORAGE_FORMAT_ZIP

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    storage_formats = sorted(definitions.STORAGE_FORMATS)

    argument_group.add_argument(
        u'--storage_format', u'--storage-format', action=u'store',
        choices=storage_formats, dest=u'storage_format', type=str,
        metavar=u'FORMAT', default=cls._DEFAULT_STORAGE_FORMAT, help=(
            u'Format of the storage file, the default is: {0:s}. Supported '
            u'options: {1:s}'.format(
                cls._DEFAULT_STORAGE_FORMAT, u', '.join(storage_formats))))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: if the storage format is not defined or supported.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          u'Configuration object is not an instance of CLITool')

    storage_format = cls._ParseStringOption(options, u'storage_format')
    if not storage_format:
      raise errors.BadConfigOption(u'Unable to determine storage format.')

    if storage_format not in definitions.STORAGE_FORMATS:
      raise errors.BadConfigOption(
          u'Unsupported storage format: {0:s}'.format(storage_format))

    setattr(configuration_object, u'_storage_format', storage_format)


manager.ArgumentHelperManager.RegisterHelper(StorageFormatArgumentsHelper)
