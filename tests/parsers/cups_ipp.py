#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Parser test for Mac Cups IPP Log files."""

import unittest

from plaso.formatters import cups_ipp  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import cups_ipp

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class CupsIppParserTest(test_lib.ParserTestCase):
  """The unit test for Mac Cups IPP parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'mac_cups_ipp'])
  def testParse(self):
    """Tests the Parse function."""
    # TODO: only tested against Mac OS X Cups IPP (Version 2.0)
    parser_object = cups_ipp.CupsIppParser()
    storage_writer = self._ParseFile(
        [u'mac_cups_ipp'], parser_object)

    self.assertEqual(len(storage_writer.events), 3)

    events = self._GetSortedEvents(storage_writer.events)

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-03 18:07:21')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(
        event.timestamp_desc,
        eventdata.EventTimestamp.CREATION_TIME)

    self.assertEqual(event.application, u'LibreOffice')
    self.assertEqual(event.job_name, u'Assignament 1')
    self.assertEqual(event.computer_name, u'localhost')
    self.assertEqual(event.copies, 1)
    self.assertEqual(event.doc_type, u'application/pdf')
    expected_job = u'urn:uuid:d51116d9-143c-3863-62aa-6ef0202de49a'
    self.assertEqual(event.job_id, expected_job)
    self.assertEqual(event.owner, u'Joaquin Moreno Garijo')
    self.assertEqual(event.user, u'moxilo')
    self.assertEqual(event.printer_id, u'RHULBW')
    expected_uri = u'ipp://localhost:631/printers/RHULBW'
    self.assertEqual(event.uri, expected_uri)
    expected_msg = (
        u'User: moxilo '
        u'Owner: Joaquin Moreno Garijo '
        u'Job Name: Assignament 1 '
        u'Application: LibreOffice '
        u'Printer: RHULBW')
    expected_msg_short = (
        u'Job Name: Assignament 1')
    self._TestGetMessageStrings(event, expected_msg, expected_msg_short)

    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-03 18:07:21')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(
        event.timestamp_desc,
        eventdata.EventTimestamp.START_TIME)

    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-03 18:07:32')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(
        event.timestamp_desc,
        eventdata.EventTimestamp.END_TIME)


if __name__ == '__main__':
  unittest.main()
