# -*- coding: utf-8 -*-
"""Output module for the Excel Spreadsheet (XLSX) output format."""

import datetime
import os
import re

import pytz
import xlsxwriter

from plaso.output import dynamic
from plaso.output import interface
from plaso.output import manager


class XLSXOutputModule(interface.OutputModule):
  """Output module for the Excel Spreadsheet (XLSX) output format."""

  NAME = 'xlsx'
  DESCRIPTION = 'Excel Spreadsheet (XLSX) output'

  WRITES_OUTPUT_FILE = True

  _DEFAULT_FIELDS = [
      'datetime', 'timestamp_desc', 'source', 'source_long',
      'message', 'parser', 'display_name', 'tag']

  _DEFAULT_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH:MM:SS.000'

  _MAXIMUM_COLUMN_WIDTH = 50
  _MINIMUM_COLUMN_WIDTH = 6

  # Illegal XML string characters.
  _ILLEGAL_XML_RE = re.compile((
      r'[\x00-\x08\x0b-\x1f\x7f-\x84\x86-\x9f\ud800-\udfff\ufdd0-\ufddf'
      r'\ufffe-\uffff]'))

  def __init__(self, output_mediator):
    """Initializes an Excel Spreadsheet (XLSX) output module.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
    """
    super(XLSXOutputModule, self).__init__(output_mediator)
    self._column_widths = []
    self._current_row = 0
    self._field_formatting_helper = dynamic.DynamicFieldFormattingHelper()
    self._fields = self._DEFAULT_FIELDS
    self._sheet = None
    self._timestamp_format = self._DEFAULT_TIMESTAMP_FORMAT
    self._workbook = None

  def _FormatDateTime(self, event, event_data):  # pylint: disable=missing-return-type-doc
    """Formats the date to a datetime object without timezone information.

    Note: timezone information must be removed due to lack of support
    by xlsxwriter and Excel.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.

    Returns:
      datetime.datetime|str: date and time value or a string containing
          "ERROR" on OverflowError.
    """
    try:
      datetime_object = datetime.datetime(
          1970, 1, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)
      datetime_object += datetime.timedelta(microseconds=event.timestamp)
      datetime_object.astimezone(self._output_mediator.timezone)

      return datetime_object.replace(tzinfo=None)

    except (OSError, OverflowError, TypeError, ValueError) as exception:
      self._ReportEventError(event, event_data, (
          'unable to copy timestamp: {0!s} to a human readable date and time '
          'with error: {1!s}. Defaulting to: "ERROR"').format(
              event.timestamp, exception))
      return 'ERROR'

  def _SanitizeField(self, field):
    """Sanitizes a field for output.

    This method replaces any illegal XML string characters with the Unicode
    replacement character (\ufffd).

    Args:
      field (str): value of the field to sanitize.

    Returns:
      str: sanitized value of the field.
    """
    return self._ILLEGAL_XML_RE.sub('\ufffd', field)

  def Close(self):
    """Closes the workbook."""
    for column_index, column_width in enumerate(self._column_widths):
      self._sheet.set_column(column_index, column_index, column_width)

    self._workbook.close()
    self._workbook = None

  def Open(self, path=None, **kwargs):  # pylint: disable=arguments-differ
    """Creates a new workbook.

    Args:
      path (Optional[str]): path of the output file.

    Raises:
      IOError: if the specified output file already exists.
      OSError: if the specified output file already exists.
      ValueError: if path is not set.
    """
    if not path:
      raise ValueError('Missing filename.')

    if os.path.isfile(path):
      raise IOError((
          'Unable to use an already existing file for output '
          '[{0:s}]').format(path))

    options = {
        'constant_memory': True,
        'strings_to_urls': False,
        'strings_to_formulas': False,
        'default_date_format': self._timestamp_format}
    self._workbook = xlsxwriter.Workbook(path, options)
    self._sheet = self._workbook.add_worksheet('Sheet')
    self._current_row = 0

  def SetFields(self, fields):
    """Sets the fields to output.

    Args:
      fields (list[str]): names of the fields to output.
    """
    self._fields = fields

  def SetTimestampFormat(self, timestamp_format):
    """Set the timestamp format to use for the datetime column.

    Args:
      timestamp_format (str): format string of date and time values.
    """
    self._timestamp_format = timestamp_format

  def WriteEventBody(self, event, event_data, event_data_stream, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """
    for column_index, field_name in enumerate(self._fields):
      if field_name == 'datetime':
        field_value = self._FormatDateTime(event, event_data)

      else:
        field_value = self._field_formatting_helper.GetFormattedField(
            self._output_mediator, field_name, event, event_data,
            event_data_stream, event_tag)
        field_value = self._SanitizeField(field_value)

      if (field_name == 'datetime' and
          isinstance(field_value, datetime.datetime)):
        self._sheet.write_datetime(
            self._current_row, column_index, field_value)
        column_width = len(self._timestamp_format) + 2
      else:
        self._sheet.write(self._current_row, column_index, field_value)
        column_width = len(field_value) + 2

      # Auto adjust the column width based on the length of the output value.
      column_width = min(column_width, self._MAXIMUM_COLUMN_WIDTH)
      column_width = max(column_width, self._MINIMUM_COLUMN_WIDTH,
                         self._column_widths[column_index])

      self._column_widths[column_index] = column_width

    self._current_row += 1

  def WriteHeader(self):
    """Writes the header to the spreadsheet."""
    cell_format = self._workbook.add_format({'bold': True})
    cell_format.set_align('center')

    self._column_widths = []
    for column_index, field_name in enumerate(self._fields):
      self._sheet.write(0, column_index, field_name, cell_format)

      column_width = len(field_name) + 2
      self._column_widths.append(column_width)

    self._current_row = 1
    self._sheet.autofilter(0, len(self._fields) - 1, 0, 0)
    self._sheet.freeze_panes(1, 0)


manager.OutputManager.RegisterOutput(XLSXOutputModule)
