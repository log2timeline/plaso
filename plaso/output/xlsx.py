# -*- coding: utf-8 -*-
"""Output module for the Excel Spreadsheet (XLSX) output format."""

from __future__ import unicode_literals

import datetime
import os
import re

try:
  import xlsxwriter
except ImportError:
  xlsxwriter = None

from plaso.lib import py2to3
from plaso.output import dynamic
from plaso.output import interface
from plaso.output import manager

import pytz  # pylint: disable=wrong-import-order


class XLSXOutputModule(interface.OutputModule):
  """Output module for the Excel Spreadsheet (XLSX) output format."""

  NAME = 'xlsx'
  DESCRIPTION = 'Excel Spreadsheet (XLSX) output'

  _DEFAULT_FIELDS = [
      'datetime', 'timestamp_desc', 'source', 'source_long',
      'message', 'parser', 'display_name', 'tag']

  _DEFAULT_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH:MM:SS.000'

  _MAX_COLUMN_WIDTH = 50
  _MIN_COLUMN_WIDTH = 6

  # Illegal Unicode characters for XML.
  _ILLEGAL_XML_RE = re.compile((
      r'[\x00-\x08\x0b-\x1f\x7f-\x84\x86-\x9f\ud800-\udfff\ufdd0-\ufddf'
      r'\ufffe-\uffff]'))

  def __init__(self, output_mediator):
    """Initializes an Excel Spreadsheet (XLSX) output module.

    Args:
      output_mediator (OutputMediator): output mediator.
    """
    super(XLSXOutputModule, self).__init__(output_mediator)
    self._column_widths = {}
    self._current_row = 0
    self._dynamic_fields_helper = dynamic.DynamicFieldsHelper(output_mediator)
    self._fields = self._DEFAULT_FIELDS
    self._filename = None
    self._sheet = None
    self._timestamp_format = self._DEFAULT_TIMESTAMP_FORMAT
    self._workbook = None

  # Pylint has trouble parsing the return type.
  # pylint: disable=missing-return-type-doc
  def _FormatDateTime(self, event, event_data):
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

    except (OverflowError, ValueError) as exception:
      self._ReportEventError(event, event_data, (
          'unable to copy timestamp: {0!s} to a human readable date and time '
          'with error: {1!s}. Defaulting to: "ERROR"').format(
              event.timestamp, exception))
      return 'ERROR'

  def _RemoveIllegalXMLCharacters(self, xml_string):
    """Removes illegal characters for XML.

    If the input is not a string it will be returned unchanged.

    Args:
      xml_string (str): XML with possible illegal characters.

    Returns:
      str: XML where all illegal characters have been removed.
    """
    if not isinstance(xml_string, py2to3.STRING_TYPES):
      return xml_string

    return self._ILLEGAL_XML_RE.sub('\ufffd', xml_string)

  def Close(self):
    """Closes the output."""
    self._workbook.close()

  def Open(self):
    """Creates a new workbook.

    Raises:
      IOError: if the specified output file already exists.
      OSError: if the specified output file already exists.
      ValueError: if the filename is not set.
    """
    if not self._filename:
      raise ValueError('Missing filename.')

    if os.path.isfile(self._filename):
      raise IOError((
          'Unable to use an already existing file for output '
          '[{0:s}]').format(self._filename))

    options = {
        'constant_memory': True,
        'strings_to_urls': False,
        'strings_to_formulas': False,
        'default_date_format': self._timestamp_format}
    self._workbook = xlsxwriter.Workbook(self._filename, options)
    self._sheet = self._workbook.add_worksheet('Sheet')
    self._current_row = 0

  def SetFields(self, fields):
    """Sets the fields to output.

    Args:
      fields (list[str]): names of the fields to output.
    """
    self._fields = fields

  def SetFilename(self, filename):
    """Sets the filename.

    Args:
      filename (str): filename.
    """
    self._filename = filename

  def SetTimestampFormat(self, timestamp_format):
    """Set the timestamp format to use for the datetime column.

    Args:
      timestamp_format (str): format string of date and time values.
    """
    self._timestamp_format = timestamp_format

  def WriteEventBody(self, event, event_data, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.
    """
    for field_name in self._fields:
      if field_name == 'datetime':
        output_value = self._FormatDateTime(event, event_data)
      else:
        output_value = self._dynamic_fields_helper.GetFormattedField(
            event, event_data, event_tag, field_name)

      output_value = self._RemoveIllegalXMLCharacters(output_value)

      # Auto adjust the column width based on the length of the output value.
      column_index = self._fields.index(field_name)
      self._column_widths.setdefault(column_index, 0)

      if field_name == 'datetime':
        column_width = min(
            self._MAX_COLUMN_WIDTH, len(self._timestamp_format) + 2)
      else:
        column_width = min(self._MAX_COLUMN_WIDTH, len(output_value) + 2)

      self._column_widths[column_index] = max(
          self._MIN_COLUMN_WIDTH, self._column_widths[column_index],
          column_width)
      self._sheet.set_column(
          column_index, column_index, self._column_widths[column_index])

      if (field_name == 'datetime'
          and isinstance(output_value, datetime.datetime)):
        self._sheet.write_datetime(
            self._current_row, column_index, output_value)
      else:
        self._sheet.write(self._current_row, column_index, output_value)

    self._current_row += 1

  def WriteHeader(self):
    """Writes the header to the spreadsheet."""
    self._column_widths = {}
    bold = self._workbook.add_format({'bold': True})
    bold.set_align('center')
    for index, field_name in enumerate(self._fields):
      self._sheet.write(self._current_row, index, field_name, bold)
      self._column_widths[index] = len(field_name) + 2
    self._current_row += 1
    self._sheet.autofilter(0, len(self._fields) - 1, 0, 0)
    self._sheet.freeze_panes(1, 0)


manager.OutputManager.RegisterOutput(
    XLSXOutputModule, disabled=xlsxwriter is None)
