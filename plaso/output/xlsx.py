# -*- coding: utf-8 -*-
"""Output module for the Excel Spreadsheet (XLSX) output format."""

import datetime
import logging
import os

try:
  import xlsxwriter
except ImportError:
  xlsxwriter = None

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
    Note: Timezone information must be removed due to lack of support
      by xlsxwriter and Excel.

    Args:
      event_object: the event object (instance of EventObject).

     Returns:
       A datetime object (instance of datetime.datetime) of the event object's
       timestamp or the Excel epoch (the null time according to Excel)
       on an OverflowError.
    """
    try:
      timestamp = timelib.Timestamp.CopyToDatetime(
          event_object.timestamp, timezone=self._output_mediator.timezone,
          raise_error=True)

      return timestamp.replace(tzinfo=None)

    except OverflowError as exception:
      logging.error((
          u'Unable to copy {0:d} into a human readable timestamp with error: '
          u'{1:s}. Event {2:d}:{3:d} triggered the exception.').format(
              event_object.timestamp, exception,
              getattr(event_object, u'store_number', u''),
              getattr(event_object, u'store_index', u'')))

      return datetime.datetime(1899, 12, 31)

  def Close(self):
    """Closes the output."""
    self._workbook.close()

  def Open(self):
    """Creates a new workbook."""
    if not self._filename:
      raise ValueError((
          u'Unable to create XlSX workbook. Output filename was not provided.'))

    if os.path.isfile(self._filename):
      raise IOError((
          u'Unable to use an already existing file for output '
          u'[{0:s}]').format(self._filename))

    self._workbook = xlsxwriter.Workbook(
        self._filename,
        {u'constant_memory': True, u'strings_to_urls': False,
         u'default_date_format': self._timestamp_format})
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
    for field in self._fields:
      callback_name = self.FIELD_FORMAT_CALLBACKS.get(field, None)
      callback_function = None
      if callback_name:
        callback_function = getattr(self, callback_name, None)

      if callback_function:
        value = callback_function(event_object)
      else:
        value = getattr(event_object, field, u'-')

      if not isinstance(value, (bool, int, long, float, datetime.datetime)):
        value = utils.GetUnicodeString(value)
        value = utils.RemoveIllegalXMLCharacters(value)

      # Auto adjust column width based on length of value.
      column_index = self._fields.index(field)
      self._column_widths.setdefault(column_index, 0)
      self._column_widths[column_index] = max(
          self._MIN_COLUMN_WIDTH,
          self._column_widths[column_index],
          min(self._MAX_COLUMN_WIDTH, len(utils.GetUnicodeString(value)) + 2))
      self._sheet.set_column(
          column_index, column_index, self._column_widths[column_index])

      if field in [u'datetime', u'timestamp']:
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
    for index, field in enumerate(self._fields):
      self._sheet.write(self._current_row, index, field, bold)
      self._column_widths[index] = len(field) + 2
    self._current_row += 1
    self._sheet.autofilter(0, len(self._fields)-1, 0, 0)
    self._sheet.freeze_panes(1, 0)


manager.OutputManager.RegisterOutput(
    XlsxOutputModule, disabled=xlsxwriter is None)

