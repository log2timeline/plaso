#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac OS X Document Versions plugin."""

import unittest

from plaso.formatters import mac_document_versions  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import mac_document_versions

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class MacDocumentVersionsTest(test_lib.SQLitePluginTestCase):
  """Tests for the Mac OS X Document Versions plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'document_versions.sql'])
  def testProcess(self):
    """Tests the Process function on a Mac OS X Document Versions file."""
    plugin_object = mac_document_versions.MacDocumentVersionsPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'document_versions.sql'], plugin_object)

    self.assertEqual(storage_writer.number_of_events, 4)

    # Check the first page visited entry.
    event_object = storage_writer.events[0]

    self.assertEqual(
        event_object.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-01-21 02:03:00')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.name, u'Spain is beautiful.rtf')
    self.assertEqual(event_object.path, u'/Users/moxilo/Documents')
    self.assertEqual(event_object.user_sid, u'501')
    expected_version_path = (
        u'/.DocumentRevisions-V100/PerUID/501/1/'
        u'com.apple.documentVersions/'
        u'08CFEB5A-5CDA-486F-AED5-EA35BF3EE4C2.rtf')
    self.assertEqual(event_object.version_path, expected_version_path)

    expected_msg = (
        u'Version of [{0:s}] ({1:s}) stored in {2:s} by {3:s}'.format(
            event_object.name, event_object.path,
            event_object.version_path, event_object.user_sid))
    expected_short = u'Stored a document version of [{0:s}]'.format(
        event_object.name)
    self._TestGetMessageStrings(event_object, expected_msg, expected_short)


if __name__ == '__main__':
  unittest.main()
