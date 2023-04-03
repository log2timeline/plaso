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

  SUPPORTS_ADDITIONAL_FIELDS = True
  SUPPORTS_CUSTOM_FIELDS = True

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

  def __init__(self):
    """Initializes an output module."""
    super(XLSXOutputModule, self).__init__()
    self._column_widths = []
    self._current_row = 0
    self._custom_fields = {}
    self._field_formatting_helper = dynamic.DynamicFieldFormattingHelper()
    self._field_names = self._DEFAULT_FIELDS
    self._sheet = None
    self._timestamp_format = self._DEFAULT_TIMESTAMP_FORMAT
    self._workbook = None

  def _FormatDateTime(self, output_mediator, event, event_data):  # pylint: disable=missing-return-type-doc
    """Formats the date to a datetime object without timezone information.

    Note: timezone information must be removed due to lack of support
    by xlsxwriter and Excel.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
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
      datetime_object.astimezone(output_mediator.time_zone)

      return datetime_object.replace(tzinfo=None)

    except (OSError, OverflowError, TypeError, ValueError) as exception:
      self._ReportEventError(event, event_data, (
          'unable to copy timestamp: {0!s} to a human readable date and time '
          'with error: {1!s}. Defaulting to: "ERROR"').format(
              event.timestamp, exception))
      return 'ERROR'

  def _GetFieldValues(
      self, output_mediator, event, event_data, event_data_stream, event_tag):
    """Retrieves the output field values.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      dict[str, str]: output field values per name.
    """
    field_values = {}
    for field_name in self._field_names:
      if field_name == 'datetime':
        field_values['datetime'] = self._FormatDateTime(
            output_mediator, event, event_data)
        continue

      field_value = self._field_formatting_helper.GetFormattedField(
          output_mediator, field_name, event, event_data, event_data_stream,
          event_tag)

      if field_value is None and field_name in self._custom_fields:
        field_value = self._custom_fields.get(field_name, None)

      if field_value is None:
        field_value = '-'
      else:
        field_value = self._SanitizeField(field_value)

      field_values[field_name] = field_value

    return field_values

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

  def _WriteFieldValues(self, output_mediator, field_values):
    """Writes field values to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_values (dict[str, str]): output field values per name.
    """
    for column_index, field_name in enumerate(self._field_names):
      field_value = field_values.get(field_name, None)
      if field_name == 'datetime' and field_value:
        self._sheet.write_datetime(self._current_row, column_index, field_value)
        column_width = len(self._timestamp_format) + 2
      else:
        field_value = field_value or ''

        self._sheet.write(self._current_row, column_index, field_value)
        column_width = len(field_value) + 2

      # Auto adjust the column width based on the length of the output value.
      column_width = min(column_width, self._MAXIMUM_COLUMN_WIDTH)
      column_width = max(column_width, self._MINIMUM_COLUMN_WIDTH,
                         self._column_widths[column_index])

      self._column_widths[column_index] = column_width

    self._current_row += 1

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

  def SetAdditionalFields(self, field_names):
    """Sets the names of additional fields to output.

    Args:
      field_names (list[str]): names of additional fields to output.
    """
    self._field_names.extend(field_names)

  def SetCustomFields(self, field_names_and_values):
    """Sets the names and values of custom fields to output.

    Args:
      field_names_and_values (list[tuple[str, str]]): names and values of
          custom fields to output.
    """
    self._custom_fields = dict(field_names_and_values)
    self._field_names.extend(self._custom_fields.keys())

  def SetFields(self, field_names):
    """Sets the names of the fields to output.

    Args:
      field_names (list[str]): names of the fields to output.
    """
    self._field_names = field_names

  def SetTimestampFormat(self, timestamp_format):
    """Set the timestamp format to use for the datetime column.

    Args:
      timestamp_format (str): format string of date and time values.
    """
    self._timestamp_format = timestamp_format

  def WriteHeader(self, output_mediator):
    """Writes the header to the spreadsheet.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
    """
    cell_format = self._workbook.add_format({'bold': True})
    cell_format.set_align('center')

    self._column_widths = []
    for column_index, field_name in enumerate(self._field_names):
      self._sheet.write(0, column_index, field_name, cell_format)

      column_width = len(field_name) + 2
      self._column_widths.append(column_width)

    self._current_row = 1
    self._sheet.autofilter(0, len(self._field_names) - 1, 0, 0)
    self._sheet.freeze_panes(1, 0)


manager.OutputManager.RegisterOutput(XLSXOutputModule)
