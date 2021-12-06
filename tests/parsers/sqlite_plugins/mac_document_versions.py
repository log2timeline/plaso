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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'mac:document_versions:file',
        'date_time': '2014-01-21 02:03:00',
        'name': 'Spain is beautiful.rtf',
        'path': '/Users/moxilo/Documents',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'user_sid': '501',
        'version_path': (
            '/.DocumentRevisions-V100/PerUID/501/1/com.apple.documentVersions/'
            '08CFEB5A-5CDA-486F-AED5-EA35BF3EE4C2.rtf')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
