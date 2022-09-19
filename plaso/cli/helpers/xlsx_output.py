# -*- coding: utf-8 -*-
"""The XLSX output module CLI arguments helper."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.output import xlsx


class XLSXOutputArgumentsHelper(interface.ArgumentsHelper):
  """XLSX output module CLI arguments helper."""

  NAME = 'xlsx'
  CATEGORY = 'output'
  DESCRIPTION = 'Argument helper for the XLSX output module.'

  _DEFAULT_FIELDS = ','.join([
      'datetime', 'timestamp_desc', 'source', 'source_long',
      'message', 'parser', 'display_name', 'tag'])

  _DEFAULT_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH:MM:SS.000'

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
        '--fields', dest='fields', type=str, action='store',
        default=cls._DEFAULT_FIELDS, help=(
            'Defines which fields should be included in the output.'))

    argument_group.add_argument(
        '--timestamp_format', dest='timestamp_format', type=str,
        action='store', default=cls._DEFAULT_TIMESTAMP_FORMAT, help=(
            'Set the timestamp format that will be used in the datetime'
            'column of the XLSX spreadsheet.'))

  @classmethod
  def ParseOptions(cls, options, output_module):  # pylint: disable=arguments-renamed
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      output_module (XLSXOutputModule): output module to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when the output filename was not provided.
    """
    if not isinstance(output_module, xlsx.XLSXOutputModule):
      raise errors.BadConfigObject(
          'Output module is not an instance of XLSXOutputModule')

    fields = cls._ParseStringOption(
        options, 'fields', default_value=cls._DEFAULT_FIELDS)

    filename = getattr(options, 'write', None)
    if not filename:
      raise errors.BadConfigOption(
          'Output filename was not provided use "-w filename" to specify.')

    timestamp_format = cls._ParseStringOption(
        options, 'timestamp_format',
        default_value=cls._DEFAULT_TIMESTAMP_FORMAT)

    output_module.SetFields([
        field_name.strip() for field_name in fields.split(',')])
    output_module.SetTimestampFormat(timestamp_format)


manager.ArgumentHelperManager.RegisterHelper(XLSXOutputArgumentsHelper)
