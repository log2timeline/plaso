#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound File (OLECF) default plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import olecf  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.olecf_plugins import default

from tests import test_lib as shared_test_lib
from tests.parsers.olecf_plugins import test_lib


class TestDefaultPluginOLECF(test_lib.OLECFPluginTestCase):
  """Tests for the OLECF default plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['Document.doc'])
  def testProcess(self):
    """Tests the Process function."""
    plugin = default.DefaultOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(
        ['Document.doc'], plugin)

    self.assertEqual(storage_writer.number_of_events, 5)

    events = list(storage_writer.GetEvents())

    # Check the Root Entry event.
    event = events[0]

    self.assertEqual(event.name, 'Root Entry')

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-05-16 02:29:49.795')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_string = (
        'Name: Root Entry')

    self._TestGetMessageStrings(event, expected_string, expected_string)

    # Check one other entry.
    event = events[1]

    expected_string = 'Name: MsoDataStore'
    self._TestGetMessageStrings(event, expected_string, expected_string)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-05-16 02:29:49.704')
    self.assertEqual(event.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
