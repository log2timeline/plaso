# -*- coding: utf-8 -*-
"""The archives CLI arguments helper."""

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class ArchivesArgumentsHelper(interface.ArgumentsHelper):
  """Archives CLI arguments helper."""

  NAME = 'archives'
  DESCRIPTION = 'Archive command line arguments.'

  _SUPPORTED_ARCHIVE_TYPES = sorted([
      'iso9660', 'modi', 'tar', 'vhdi', 'zip'])

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
        '--archives', dest='archives', type=str, action='store', default='none',
        metavar='TYPES', help=(
            'Define a list of archive and storage media image types for which '
            'to process embedded file entries, such as TAR (archive.tar) or '
            'ZIP (archive.zip). This is a comma separated list where each '
            'entry is the name of an archive type, such as "tar,zip". "all" '
            'indicates that all archive types should be enabled. "none" '
            'disables processing file entries embedded in archives. Use '
            '"--archives list" to list the available archive types. WARNING: '
            'this can make processing significantly slower.'))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    archives = getattr(options, 'archives', 'none')

    if archives == 'all':
      archives = ','.join(cls._SUPPORTED_ARCHIVE_TYPES)
    elif archives not in ('list', 'none'):
      for archive_type in archives.split(','):
        if archive_type not in cls._SUPPORTED_ARCHIVE_TYPES:
          raise errors.BadConfigOption(
               'Unsupported archive types: {0:s}.'.format(archives))

    setattr(configuration_object, '_archive_types_string', archives)


manager.ArgumentHelperManager.RegisterHelper(ArchivesArgumentsHelper)
