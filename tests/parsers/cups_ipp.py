#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Parser test for MacOS Cups IPP Log files."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import cups_ipp as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers import cups_ipp

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class CupsIppParserTest(test_lib.ParserTestCase):
  """Tests for MacOS Cups IPP parser."""

  @shared_test_lib.skipUnlessHasTestFile(['mac_cups_ipp'])
  def testParse(self):
    """Tests the Parse function."""
    # TODO: only tested against MacOS Cups IPP (Version 2.0)
    parser = cups_ipp.CupsIppParser()
    storage_writer = self._ParseFile(['mac_cups_ipp'], parser)

    self.assertEqual(storage_writer.number_of_events, 3)

    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-11-03 18:07:21.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    self.assertEqual(event.application, 'LibreOffice')
    self.assertEqual(event.job_name, 'Assignament 1')
    self.assertEqual(event.computer_name, 'localhost')
    self.assertEqual(event.copies, 1)
    self.assertEqual(event.doc_type, 'application/pdf')
    self.assertEqual(
        event.job_id, 'urn:uuid:d51116d9-143c-3863-62aa-6ef0202de49a')
    self.assertEqual(event.owner, 'Joaquin Moreno Garijo')
    self.assertEqual(event.user, 'moxilo')
    self.assertEqual(event.printer_id, 'RHULBW')
    self.assertEqual(event.uri, 'ipp://localhost:631/printers/RHULBW')

    expected_message = (
        'User: moxilo '
        'Owner: Joaquin Moreno Garijo '
        'Job Name: Assignament 1 '
        'Application: LibreOffice '
        'Printer: RHULBW')
    expected_short_message = 'Job Name: Assignament 1'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-11-03 18:07:21.000000')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_START)

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2013-11-03 18:07:32.000000')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_END)


if __name__ == '__main__':
  unittest.main()
