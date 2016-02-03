# -*- coding: utf-8 -*-
"""Output module for the Excel Spreadsheet (XLSX) output format."""

import os
import re

try:
  import xlsxwriter
except ImportError:
  xlsxwriter = None

from plaso.lib import py2to3
from plaso.lib import timelib
from plaso.output import dynamic
from plaso.output import interface
from plaso.output import manager


class XLSXOutputModule(interface.OutputModule):
  """Output module for the Excel Spreadsheet (XLSX) output format."""

  NAME = u'xlsx'
  DESCRIPTION = u'Excel Spreadsheet (XLSX) output'

  _DEFAULT_FIELDS = [
      u'datetime', u'timestamp_desc', u'source', u'source_long',
      u'message', u'parser', u'display_name', u'tag']

  _DEFAULT_TIMESTAMP_FORMAT = u'YYYY-MM-DD HH:MM:SS.000'

  _MAX_COLUMN_WIDTH = 50
  _MIN_COLUMN_WIDTH = 6

  # Illegal Unicode characters for XML.
  _ILLEGAL_XML_RE = re.compile((
      ur'[\x00-\x08\x0b-\x1f\x7f-\x84\x86-\x9f\ud800-\udfff\ufdd0-\ufddf'
      ur'\ufffe-\uffff]'))

  def __init__(self, output_mediator):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
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

  def _FormatDateTime(self, event_object):
    """Formats the date to a datetime object without timezone information.

    Note: timezone information must be removed due to lack of support
    by xlsxwriter and Excel.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A datetime object (instance of datetime.datetime)
      or a string containing 'ERROR' on OverflowError.
    """
    try:
      timestamp = timelib.Timestamp.CopyToDatetime(
          event_object.timestamp, self._output_mediator.timezone,
          raise_error=True)

      return timestamp.replace(tzinfo=None)

    except OverflowError as exception:
      self._ReportEventError(event_object, (
          u'unable to copy timestamp: {0:d} to a human readable date and time '
          u'with error: {1:s}. Defaulting to: "ERROR"').format(
              event_object.timestamp, exception))
      return u'ERROR'

  def _RemoveIllegalXMLCharacters(self, xml_string):
    """Removes illegal characters for XML.

    Args:
      xml_string: a string containing XML with possible illegal characters.

    Returns:
      A string containing XML where all illegal characters have been removed.
      If the input is not a string it will be returned unchanged.
    """
    if not isinstance(xml_string, py2to3.STRING_TYPES):
      return xml_string

    return self._ILLEGAL_XML_RE.sub(u'\ufffd', xml_string)

  def Close(self):
    """Closes the output."""
    self._workbook.close()

  def Open(self):
    """Creates a new workbook.

    Raises:
      IOError: if the specified output file already exists.
      ValueError: if the filename is not set.
    """
    if not self._filename:
      raise ValueError(u'Missing filename.')

    if os.path.isfile(self._filename):
      raise IOError((
          u'Unable to use an already existing file for output '
          u'[{0:s}]').format(self._filename))

    options = {
        u'constant_memory': True,
        u'strings_to_urls': False,
        u'strings_to_formulas': False,
        u'default_date_format': self._timestamp_format}
    self._workbook = xlsxwriter.Workbook(self._filename, options)
    self._sheet = self._workbook.add_worksheet(u'Sheet')
    self._current_row = 0

  def SetFields(self, fields):
    """Sets the fields to output.

    Args:
      fields: a list of strings containing the names of the fields to output.
    """
    self._fields = fields

  def SetFilename(self, filename):
    """Sets the filename.

    Args:
      filename: the filename.
    """
    self._filename = filename

  def SetTimestampFormat(self, timestamp_format):
    """Set the timestamp format to use for the datetime column.

    Args:
      timestamp_format: A string that describes the way to format the datetime.
    """
    self._timestamp_format = timestamp_format

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the spreadsheet.

    Args:
      event_object: the event object (instance of EventObject).
    """
    for field_name in self._fields:
      if field_name == u'datetime':
        output_value = self._FormatDateTime(event_object)
      else:
        output_value = self._dynamic_fields_helper.GetFormattedField(
            event_object, field_name)

      output_value = self._RemoveIllegalXMLCharacters(output_value)

      # Auto adjust the column width based on the length of the output value.
      column_index = self._fields.index(field_name)
      self._column_widths.setdefault(column_index, 0)

      if field_name == u'datetime':
        column_width = min(
            self._MAX_COLUMN_WIDTH, len(self._timestamp_format) + 2)
      else:
        column_width = min(self._MAX_COLUMN_WIDTH, len(output_value) + 2)

      self._column_widths[column_index] = max(
          self._MIN_COLUMN_WIDTH, self._column_widths[column_index],
          column_width)
      self._sheet.set_column(
          column_index, column_index, self._column_widths[column_index])

      if field_name == u'datetime':
        self._sheet.write_datetime(
            self._current_row, column_index, output_value)
      else:
        self._sheet.write(self._current_row, column_index, output_value)

    self._current_row += 1

  def WriteHeader(self):
    """Writes the header to the spreadsheet."""
    self._column_widths = {}
    bold = self._workbook.add_format({u'bold': True})
    bold.set_align(u'center')
    for index, field_name in enumerate(self._fields):
      self._sheet.write(self._current_row, index, field_name, bold)
      self._column_widths[index] = len(field_name) + 2
    self._current_row += 1
    self._sheet.autofilter(0, len(self._fields) - 1, 0, 0)
    self._sheet.freeze_panes(1, 0)


manager.OutputManager.RegisterOutput(
    XLSXOutputModule, disabled=xlsxwriter is None)
