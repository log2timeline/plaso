#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS Document Versions plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mac_document_versions as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import mac_document_versions

from tests.parsers.sqlite_plugins import test_lib


class MacDocumentVersionsTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacOS Document Versions plugin."""

  def testProcess(self):
    """Tests the Process function on a MacOS Document Versions file."""
    plugin = mac_document_versions.MacDocumentVersionsPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['document_versions.sql'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetEvents())

    # Check the first page visited entry.
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2014-01-21 02:03:00.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.name, 'Spain is beautiful.rtf')
    self.assertEqual(event_data.path, '/Users/moxilo/Documents')
    self.assertEqual(event_data.user_sid, '501')
    expected_version_path = (
        '/.DocumentRevisions-V100/PerUID/501/1/'
        'com.apple.documentVersions/'
        '08CFEB5A-5CDA-486F-AED5-EA35BF3EE4C2.rtf')
    self.assertEqual(event_data.version_path, expected_version_path)

    expected_message = (
        'Version of [{0:s}] ({1:s}) stored in {2:s} by {3:s}'.format(
            event_data.name, event_data.path, event_data.version_path,
            event_data.user_sid))
    expected_short_message = 'Stored a document version of [{0:s}]'.format(
        event_data.name)
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
