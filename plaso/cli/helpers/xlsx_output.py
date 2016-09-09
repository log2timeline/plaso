# -*- coding: utf-8 -*-
"""The XLSX output module CLI arguments helper."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.output import xlsx


class XLSXOutputArgumentsHelper(interface.ArgumentsHelper):
  """XLSX output module CLI arguments helper."""

  NAME = u'xlsx'
  CATEGORY = u'output'
  DESCRIPTION = u'Argument helper for the XLSX output module.'

  _DEFAULT_FIELDS = u','.join([
      u'datetime', u'timestamp_desc', u'source', u'source_long',
      u'message', u'parser', u'display_name', u'tag'])

  _DEFAULT_TIMESTAMP_FORMAT = u'YYYY-MM-DD HH:MM:SS.000'

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
        u'--fields', dest=u'fields', type=str, action=u'store',
        default=cls._DEFAULT_FIELDS, help=(
            u'Defines which fields should be included in the output.'))
    argument_group.add_argument(
        u'--additional_fields', dest=u'additional_fields', type=str,
        action=u'store', default=u'', help=(
            u'Defines extra fields to be included in the output, in addition to'
            u' the default fields, which are {0:s}.'.format(
                cls._DEFAULT_FIELDS)))
    argument_group.add_argument(
        u'--timestamp_format', dest=u'timestamp_format', type=str,
        action=u'store', default=cls._DEFAULT_TIMESTAMP_FORMAT, help=(
            u'Set the timestamp format that will be used in the datetime'
            u'column of the XLSX spreadsheet.'))

  @classmethod
  def ParseOptions(cls, options, output_module):
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
          u'Output module is not an instance of XLSXOutputModule')

    fields = cls._ParseStringOption(
        options, u'fields', default_value=cls._DEFAULT_FIELDS)

    additional_fields = cls._ParseStringOption(options, u'additional_fields')

    if additional_fields:
      fields = u'{0:s},{1:s}'.format(fields, additional_fields)

    filename = getattr(options, u'write', None)
    if not filename:
      raise errors.BadConfigOption(
          u'Output filename was not provided use "-w filename" to specify.')

    timestamp_format = cls._ParseStringOption(
        options, u'timestamp_format',
        default_value=cls._DEFAULT_TIMESTAMP_FORMAT)

    output_module.SetFields([
        field_name.strip() for field_name in fields.split(u',')])
    output_module.SetFilename(filename)
    output_module.SetTimestampFormat(timestamp_format)


manager.ArgumentHelperManager.RegisterHelper(XLSXOutputArgumentsHelper)
