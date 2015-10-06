# -*- coding: utf-8 -*-
"""The arguments helper for the xlsx output module."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.output import xlsx


class XlsxOutputHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for the XLSX output module."""

  NAME = u'xlsx'
  CATEGORY = u'output'
  DESCRIPTION = u'Argument helper for the XLSX output module.'

  _DEFAULT_TIMESTAMP_FORMAT = u'YYYY-MM-DD HH:MM:SS.000'

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
        u'--timestamp_format', dest=u'timestamp_format', type=str,
        action=u'store', default=cls._DEFAULT_TIMESTAMP_FORMAT, help=(
            u'Set the timestamp format that will be used in the datetime'
            u'column of the XLSX spreadsheet.'))

  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options: the parser option object (instance of argparse.Namespace).
      output_module: an output module (instance of OutputModule).

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
    """
    if not isinstance(output_module, xlsx.XlsxOutputModule):
      raise errors.BadConfigObject(
          u'Output module is not an instance of XlsxOutputModule')

    timestamp_format = cls._ParseStringOption(
        options, u'timestamp_format',
        default_value=cls._DEFAULT_TIMESTAMP_FORMAT)
    output_module.SetTimestampFormat(timestamp_format)

    filename = getattr(options, u'write', None)
    if filename:
      output_module.SetFilename(filename)


manager.ArgumentHelperManager.RegisterHelper(XlsxOutputHelper)
