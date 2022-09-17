# -*- coding: utf-8 -*-
"""The extraction CLI arguments helper."""

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class ExtractionArgumentsHelper(interface.ArgumentsHelper):
  """Extraction CLI arguments helper."""

  NAME = 'extraction'
  DESCRIPTION = 'Extraction command line arguments.'

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
        '--preferred_year', '--preferred-year', dest='preferred_year',
        type=int, action='store', default=None, metavar='YEAR', help=(
            'When a format\'s timestamp does not include a year, e.g. '
            'syslog, use this as the initial year instead of attempting '
            'auto-detection.'))

    argument_group.add_argument(
        '--process_archives', '--process-archives', dest='process_archives',
        action='store_true', default=False, help=(
            'Process file entries embedded within archive files, such as '
            'archive.tar and archive.zip. This can make processing '
            'significantly slower. WARNING: this option is deprecated use '
            '--archives=tar,zip instead.'))

    argument_group.add_argument(
        '--skip_compressed_streams', '--skip-compressed-streams',
        dest='process_compressed_streams', action='store_false', default=True,
        help=(
            'Skip processing file content within compressed streams, such as '
            'syslog.gz and syslog.bz2.'))

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
          'Configuration object is not an instance of CLITool')

    preferred_year = cls._ParseNumericOption(options, 'preferred_year')

    process_archives = getattr(options, 'process_archives', False)
    process_compressed_streams = getattr(
        options, 'process_compressed_streams', True)

    setattr(configuration_object, '_preferred_year', preferred_year)
    setattr(configuration_object, '_process_archives', process_archives)
    setattr(
        configuration_object, '_process_compressed_streams',
        process_compressed_streams)


manager.ArgumentHelperManager.RegisterHelper(ExtractionArgumentsHelper)
