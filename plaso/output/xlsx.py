# -*- coding: utf-8 -*-
"""Output module for the Excel Spreadsheet (XLSX) output format."""

import datetime
import logging
import os

try:
  import xlsxwriter
except ImportError:
  xlsxwriter = None

from plaso.lib import py2to3
from plaso.lib import timelib
from plaso.lib import utils
from plaso.output import dynamic
from plaso.output import manager


class XlsxOutputModule(dynamic.DynamicOutputModule):
  """Output module for the Excel Spreadsheet (XLSX) output format."""

  NAME = u'xlsx'
  DESCRIPTION = u'Excel Spreadsheet (XLSX) output'

  _MAX_COLUMN_WIDTH = 50
  _MIN_COLUMN_WIDTH = 6

  def __init__(self, output_mediator):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
    """
    super(XlsxOutputModule, self).__init__(output_mediator)
    self._column_widths = {}
    self._current_row = 0
    self._filename = None
    self._sheet = None
    self._timestamp_format = None
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
      event_storage_identifier = self._GetEventStorageIdentifier(event_object)
      logging.error((
          u'Unable to copy timestamp: {0:d} from event: {1:s} into a human '
          u'readable date and time with error: {2:s}. Defaulting to: '
          u'"ERROR"').format(
              event_object.timestamp, event_storage_identifier, exception))
      logging.error(
          u'Event: {0:s} data type: {1:s} display name: {2:s}'.format(
              event_storage_identifier, event_object.data_type,
              event_object.display_name))

      return u'ERROR'

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
      callback_name = self.FIELD_FORMAT_CALLBACKS.get(field_name, None)
      callback_function = None
      if callback_name:
        callback_function = getattr(self, callback_name, None)

      if callback_function:
        value = callback_function(event_object)
      else:
        value = getattr(event_object, field_name, u'-')

      if not isinstance(value, (
          bool, py2to3.INTEGER_TYPES, float, datetime.datetime)):
        value = utils.GetUnicodeString(value)
        value = utils.RemoveIllegalXMLCharacters(value)

      # Auto adjust column width based on length of value.
      column_index = self._fields.index(field_name)
      self._column_widths.setdefault(column_index, 0)
      self._column_widths[column_index] = max(
          self._MIN_COLUMN_WIDTH,
          self._column_widths[column_index],
          min(self._MAX_COLUMN_WIDTH, len(utils.GetUnicodeString(value)) + 2))
      self._sheet.set_column(
          column_index, column_index, self._column_widths[column_index])

      if isinstance(value, datetime.datetime):
        self._sheet.write_datetime(
            self._current_row, column_index, value)
      else:
        self._sheet.write(self._current_row, column_index, value)

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
    XlsxOutputModule, disabled=xlsxwriter is None)
