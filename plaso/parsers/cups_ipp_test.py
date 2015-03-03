#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Parser test for Mac Cups IPP Log files."""

import unittest

from plaso.formatters import cups_ipp as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import cups_ipp
from plaso.parsers import test_lib


class CupsIppParserTest(test_lib.ParserTestCase):
  """The unit test for Mac Cups IPP parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = cups_ipp.CupsIppParser()

  def testParse(self):
    """Tests the Parse function."""
    # TODO: only tested against Mac OS X Cups IPP (Version 2.0)
    test_file = self._GetTestFilePath([u'mac_cups_ipp'])
    events = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(events)

    self.assertEqual(len(event_objects), 3)
    event_object = event_objects[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-11-03 18:07:21')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(
        event_object.timestamp_desc,
        eventdata.EventTimestamp.CREATION_TIME)
    self.assertEqual(event_object.application, u'LibreOffice')
    self.assertEqual(event_object.job_name, u'Assignament 1')
    self.assertEqual(event_object.computer_name, u'localhost')
    self.assertEqual(event_object.copies, 1)
    self.assertEqual(event_object.doc_type, u'application/pdf')
    expected_job = u'urn:uuid:d51116d9-143c-3863-62aa-6ef0202de49a'
    self.assertEqual(event_object.job_id, expected_job)
    self.assertEqual(event_object.owner, u'Joaquin Moreno Garijo')
    self.assertEqual(event_object.user, u'moxilo')
    self.assertEqual(event_object.printer_id, u'RHULBW')
    expected_uri = u'ipp://localhost:631/printers/RHULBW'
    self.assertEqual(event_object.uri, expected_uri)
    expected_msg = (
        u'User: moxilo '
        u'Owner: Joaquin Moreno Garijo '
        u'Job Name: Assignament 1 '
        u'Application: LibreOffice '
        u'Printer: RHULBW')
    expected_msg_short = (
        u'Job Name: Assignament 1')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-11-03 18:07:21')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(
        event_object.timestamp_desc,
        eventdata.EventTimestamp.START_TIME)

    event_object = event_objects[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-11-03 18:07:32')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(
        event_object.timestamp_desc,
        eventdata.EventTimestamp.END_TIME)


if __name__ == '__main__':
  unittest.main()
