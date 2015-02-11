#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac OS X Document Versions plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import mac_document_versions as mac_doc_rev_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers.sqlite_plugins import mac_document_versions
from plaso.parsers.sqlite_plugins import test_lib


class MacDocumentVersionsTest(test_lib.SQLitePluginTestCase):
  """Tests for the Mac OS X Document Versions plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = mac_document_versions.MacDocumentVersionsPlugin()

  def testProcess(self):
    """Tests the Process function on a Mac OS X Document Versions file."""
    test_file = self._GetTestFilePath(['document_versions.sql'])
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 4)

    # Check the first page visited entry.
    event_object = event_objects[0]

    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2014-01-21 02:03:00')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    self.assertEquals(event_object.name, u'Spain is beautiful.rtf')
    self.assertEquals(event_object.path, u'/Users/moxilo/Documents')
    self.assertEquals(event_object.user_sid, u'501')
    expected_version_path = (
        u'/.DocumentRevisions-V100/PerUID/501/1/'
        u'com.apple.documentVersions/'
        u'08CFEB5A-5CDA-486F-AED5-EA35BF3EE4C2.rtf')
    self.assertEquals(event_object.version_path, expected_version_path)

    expected_msg = (
        u'Version of [{0:s}] ({1:s}) stored in {2:s} by {3:s}'.format(
            event_object.name, event_object.path,
            event_object.version_path, event_object.user_sid))
    expected_short = u'Stored a document version of [{0:s}]'.format(
        event_object.name)
    self._TestGetMessageStrings(event_object, expected_msg, expected_short)


if __name__ == '__main__':
  unittest.main()
