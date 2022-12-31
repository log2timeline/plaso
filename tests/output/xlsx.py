#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the XLSX output module."""

import datetime
import os
import unittest
import zipfile

from defusedxml import ElementTree

from plaso.containers import events
from plaso.lib import definitions
from plaso.output import xlsx

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class XLSXOutputModuleTest(test_lib.OutputModuleTestCase):
  """Test the XLSX output module."""

  # pylint: disable=protected-access

  _SHARED_STRINGS = 'xl/sharedStrings.xml'
  _SHEET1 = 'xl/worksheets/sheet1.xml'

  _COLUMN_TAG = '}c'
  _ROW_TAG = '}row'
  _SHARED_STRING_TAG = '}t'
  _SHARED_STRING_TYPE = 's'
  _TYPE_ATTRIBUTE = 't'
  _VALUE_STRING_TAG = '}v'

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'hostname': 'ubuntu',
       'filename': 'log/syslog.1',
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root) Invalid character -> \ud801'),
       'timestamp': '2012-06-27 18:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_METADATA_MODIFICATION}]

  def _GetSheetRows(self, filename):
    """Parses the contents of the first sheet of an XLSX document.

    Args:
      filename (str): The file path of the XLSX document to parse.

    Returns:
      list[list[str]]: A list of lists representing the rows of the first sheet.

    Raises:
      ValueError: if the sheet cannot be found, or a string cannot be read.
    """
    rows = []
    with zipfile.ZipFile(filename) as zip_file:
      if self._SHEET1 not in zip_file.namelist():
        # Fail if we cannot find the expected first sheet.
        raise ValueError('Unable to locate expected sheet: {0:s}'.format(
            self._SHEET1))

      # Generate a reference table of shared strings if available.
      strings = []
      if self._SHARED_STRINGS in zip_file.namelist():
        with zip_file.open(self._SHARED_STRINGS) as zip_file_object:
          for _, element in ElementTree.iterparse(zip_file_object):
            if element.tag.endswith(self._SHARED_STRING_TAG):
              strings.append(element.text)

      row = []
      value = ''
      with zip_file.open(self._SHEET1) as zip_file_object:
        for _, element in ElementTree.iterparse(zip_file_object):
          if (element.tag.endswith(self._VALUE_STRING_TAG) or
              element.tag.endswith(self._SHARED_STRING_TAG)):
            value = element.text

          if element.tag.endswith(self._COLUMN_TAG):
            # Grab value from shared string reference table if type shared
            # string.
            if strings and element.attrib.get(
                self._TYPE_ATTRIBUTE) == self._SHARED_STRING_TYPE:
              try:
                value = strings[int(value)]
              except (IndexError, ValueError):
                raise ValueError(
                    'Unable to successfully dereference shared string.')

            row.append(value)

          # If we see the end tag of the row, record row in rows and reset.
          if element.tag.endswith(self._ROW_TAG):
            rows.append(row)
            row = []

    return rows

  def testGetFieldValues(self):
    """Tests the _GetFieldValues function."""
    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = xlsx.XLSXOutputModule()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    event_tag = events.EventTag()
    event_tag.AddLabels(['Malware', 'Printed'])

    expected_field_values = {
        'datetime': datetime.datetime(2012, 6, 27, 18, 17, 1),
        'display_name': '-',
        'message': (
            'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
            'closed for user root) Invalid character -> �'),
        'parser': '-',
        'source': 'FILE',
        'source_long': 'Test log file',
        'tag': 'Malware Printed',
        'timestamp_desc': 'Metadata Modification Time'}

    field_values = output_module._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

    self.assertEqual(field_values, expected_field_values)

  def testWriteFieldValues(self):
    """Tests the _WriteFieldValues function."""
    output_mediator = self._CreateOutputMediator()

    formatters_directory_path = self._GetTestFilePath(['formatters'])
    output_mediator.ReadMessageFormattersFromDirectory(
        formatters_directory_path)

    output_module = xlsx.XLSXOutputModule()

    with shared_test_lib.TempDirectory() as temp_directory:
      xslx_file = os.path.join(temp_directory, 'xlsx.out')

      event, event_data, event_data_stream = (
          containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

      event_tag = events.EventTag()
      event_tag.AddLabels(['Malware', 'Printed'])

      output_module.Open(path=xslx_file)

      try:
        output_module.WriteHeader(output_mediator)

        field_values = output_module._GetFieldValues(
            output_mediator, event, event_data, event_data_stream, event_tag)

        output_module._WriteFieldValues(output_mediator, field_values)

      finally:
        output_module.Close()

      try:
        rows = self._GetSheetRows(xslx_file)
      except ValueError as exception:
        self.fail(exception)

      expected_header = [
          'datetime', 'timestamp_desc', 'source', 'source_long',
          'message', 'parser', 'display_name', 'tag']
      expected_event_body = [
          '41087.76181712963', 'Metadata Modification Time', 'FILE',
          'Test log file',
          'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session '
          'closed for user root) Invalid character -> \ufffd',
          '-', '-', 'Malware Printed']

      self.assertEqual(expected_header, rows[0])
      self.assertEqual(len(expected_event_body), len(rows[1]))
      self.assertEqual(expected_event_body, rows[1])

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    expected_header = [
        'datetime', 'timestamp_desc', 'source', 'source_long',
        'message', 'parser', 'display_name', 'tag']

    with shared_test_lib.TempDirectory() as temp_directory:
      output_mediator = self._CreateOutputMediator()
      output_module = xlsx.XLSXOutputModule()

      xlsx_file = os.path.join(temp_directory, 'xlsx.out')

      output_module.Open(path=xlsx_file)

      try:
        output_module.WriteHeader(output_mediator)
      finally:
        output_module.Close()

      try:
        rows = self._GetSheetRows(xlsx_file)
      except ValueError as exception:
        self.fail(exception)

      self.assertEqual(expected_header, rows[0])


if __name__ == '__main__':
  unittest.main()
