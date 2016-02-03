#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the XLSX output module."""

import os
import unittest
import zipfile

from xml.etree import ElementTree

from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.output import xlsx

from tests import test_lib as shared_test_lib
from tests.output import test_lib


class TestEvent(event.EventObject):
  DATA_TYPE = u'test:xlsx'

  def __init__(self):
    super(TestEvent, self).__init__()
    self.timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01')
    self.timestamp_desc = eventdata.EventTimestamp.CHANGE_TIME
    self.hostname = u'ubuntu'
    self.filename = u'log/syslog.1'
    self.text = (
        u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
        u'closed for user root) Invalid character -> \ud801')

class TestEventFormatter(formatters_interface.EventFormatter):
  DATA_TYPE = u'test:xlsx'
  FORMAT_STRING = u'{text}'

  SOURCE_SHORT = u'LOG'
  SOURCE_LONG = u'Syslog'


class XLSXOutputModuleTest(test_lib.OutputModuleTestCase):
  """Test the XLSX output module."""

  _SHARED_STRINGS = u'xl/sharedStrings.xml'
  _SHEET1 = u'xl/worksheets/sheet1.xml'

  _COLUMN_TAG = u'}c'
  _ROW_TAG = u'}row'
  _SHARED_STRING_TAG = u'}t'
  _SHARED_STRING_TYPE = u's'
  _TYPE_ATTRIBUTE = u't'
  _VALUE_STRING_TAG = u'}v'

  def _GetSheetRows(self, filename):
    """Parses the contents of the first sheet of an XLSX document.

    Args:
      filename: The file path of the XLSX document to parse.

    Returns:
      A list of dictionaries representing the rows and columns of the first
      sheet.
    """

    zip_file = zipfile.ZipFile(filename)

    # Fail if we can't find the expected first sheet.
    if self._SHEET1 not in zip_file.namelist():
      raise ValueError(
          u'Unable to locate expected sheet: {0:s}'.format(self._SHEET1))

    # Generate a reference table of shared strings if available.
    strings = []
    if self._SHARED_STRINGS in zip_file.namelist():
      zip_file_object = zip_file.open(self._SHARED_STRINGS)
      for _, element in ElementTree.iterparse(zip_file_object):
        if element.tag.endswith(self._SHARED_STRING_TAG):
          strings.append(element.text)

    row = []
    rows = []
    value = u''
    zip_file_object = zip_file.open(self._SHEET1)
    for _, element in ElementTree.iterparse(zip_file_object):
      if (element.tag.endswith(self._VALUE_STRING_TAG) or
          element.tag.endswith(self._SHARED_STRING_TAG)):
        value = element.text

      if element.tag.endswith(self._COLUMN_TAG):
        # Grab value from shared string reference table if type shared string.
        if (strings and element.attrib.get(self._TYPE_ATTRIBUTE) ==
            self._SHARED_STRING_TYPE):
          try:
            value = strings[int(value)]
          except (IndexError, ValueError):
            raise ValueError(
                u'Unable to successfully dereference shared string.')

        row.append(value)

      # If we see the end tag of the row, record row in rows and reset.
      if element.tag.endswith(self._ROW_TAG):
        rows.append(row)
        row = []

    return rows

  def testHeader(self):
    """Tests the WriteHeader function."""

    expected_header = [
        u'datetime', u'timestamp_desc', u'source', u'source_long',
        u'message', u'parser', u'display_name', u'tag']

    with shared_test_lib.TempDirectory() as temp_directory:
      output_mediator = self._CreateOutputMediator()
      output_module = xlsx.XLSXOutputModule(output_mediator)

      xlsx_file = os.path.join(temp_directory, u'xlsx.out')
      output_module.SetFilename(xlsx_file)

      output_module.Open()
      output_module.WriteHeader()
      output_module.WriteFooter()
      output_module.Close()

      try:
        rows = self._GetSheetRows(xlsx_file)
      except ValueError as exception:
        self.fail(exception)

      self.assertEqual(expected_header, rows[0])

  def testWriteEventBody(self):
    """Tests the WriteHeader function."""
    formatters_manager.FormattersManager.RegisterFormatter(TestEventFormatter)

    expected_header = [
        u'datetime', u'timestamp_desc', u'source', u'source_long',
        u'message', u'parser', u'display_name', u'tag']
    expected_event_body = [
        u'41087.7618171296', u'Metadata Modification Time', u'LOG', u'Syslog',
        u'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
        u'closed for user root) Invalid character -> \ufffd',
        u'-', u'-', u'-']

    with shared_test_lib.TempDirectory() as temp_directory:
      output_mediator = self._CreateOutputMediator()
      output_module = xlsx.XLSXOutputModule(output_mediator)

      xslx_file = os.path.join(temp_directory, u'xlsx.out')
      output_module.SetFilename(xslx_file)

      output_module.Open()
      output_module.WriteHeader()
      output_module.WriteEvent(TestEvent())
      output_module.WriteFooter()
      output_module.Close()

      try:
        rows = self._GetSheetRows(xslx_file)
      except ValueError as exception:
        self.fail(exception)

      self.assertEqual(expected_header, rows[0])
      self.assertEqual(len(expected_event_body), len(rows[1]))
      self.assertEqual(expected_event_body, rows[1])


if __name__ == u'__main__':
  unittest.main()

