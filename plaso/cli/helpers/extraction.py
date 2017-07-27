# -*- coding: utf-8 -*-
"""The extraction CLI arguments helper."""

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class ExtractionArgumentsHelper(interface.ArgumentsHelper):
  """Extraction CLI arguments helper."""

  NAME = u'extraction'
  DESCRIPTION = u'Extraction command line arguments.'

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
        u'--preferred_year', u'--preferred-year', dest=u'preferred_year',
        action=u'store', default=None, metavar=u'YEAR', help=(
            u'When a format\'s timestamp does not include a year, e.g. '
            u'syslog, use this as the initial year instead of attempting '
            u'auto-detection.'))

    argument_group.add_argument(
        u'-p', u'--preprocess', dest=u'preprocess', action=u'store_true',
        default=False, help=(
            u'Turn on preprocessing. Preprocessing is turned on by default '
            u'when parsing image files, however if a mount point is being '
            u'parsed then this parameter needs to be set manually.'))

    argument_group.add_argument(
        u'--process_archives', u'--process-archives', dest=u'process_archives',
        action=u'store_true', default=False, help=(
            u'Process file entries embedded within archive files, such as '
            u'archive.tar and archive.zip. This can make processing '
            u'significantly slower.'))

    argument_group.add_argument(
        u'--skip_compressed_streams', u'--skip-compressed-streams',
        dest=u'process_compressed_streams', action=u'store_false', default=True,
        help=(
            u'Skip processing file content within compressed streams, such as '
            u'syslog.gz and syslog.bz2.'))

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

    preprocess = getattr(options, u'preprocess', False)

    preferred_year = cls._ParseNumericOption(options, u'preferred_year')

    process_archives = getattr(options, u'process_archives', False)
    process_compressed_streams = getattr(
        options, u'process_compressed_streams', True)

    setattr(configuration_object, u'_force_preprocessing', preprocess)
    setattr(configuration_object, u'_preferred_year', preferred_year)
    setattr(configuration_object, u'_process_archives', process_archives)
    setattr(
        configuration_object, u'_process_compressed_streams',
        process_compressed_streams)


manager.ArgumentHelperManager.RegisterHelper(ExtractionArgumentsHelper)
