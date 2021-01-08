#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS Document Versions plugin."""

import unittest

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

    expected_event_values = {
        'data_type': 'mac:document_versions:file',
        'name': 'Spain is beautiful.rtf',
        'path': '/Users/moxilo/Documents',
        'timestamp': '2014-01-21 02:03:00.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'user_sid': '501',
        'version_path': (
            '/.DocumentRevisions-V100/PerUID/501/1/com.apple.documentVersions/'
            '08CFEB5A-5CDA-486F-AED5-EA35BF3EE4C2.rtf')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
