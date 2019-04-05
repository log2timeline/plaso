#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS Document Versions plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mac_document_versions as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import mac_document_versions

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class MacDocumentVersionsTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacOS Document Versions plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['document_versions.sql'])
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

    self.assertEqual(event.name, 'Spain is beautiful.rtf')
    self.assertEqual(event.path, '/Users/moxilo/Documents')
    self.assertEqual(event.user_sid, '501')
    expected_version_path = (
        '/.DocumentRevisions-V100/PerUID/501/1/'
        'com.apple.documentVersions/'
        '08CFEB5A-5CDA-486F-AED5-EA35BF3EE4C2.rtf')
    self.assertEqual(event.version_path, expected_version_path)

    expected_message = (
        'Version of [{0:s}] ({1:s}) stored in {2:s} by {3:s}'.format(
            event.name, event.path, event.version_path, event.user_sid))
    expected_short_message = 'Stored a document version of [{0:s}]'.format(
        event.name)
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
