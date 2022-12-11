#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS Document Versions plugin."""

import unittest

from plaso.parsers.sqlite_plugins import macos_document_versions

from tests.parsers.sqlite_plugins import test_lib


class MacOSDocumentVersionsTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacOS Document Versions plugin."""

  def testProcess(self):
    """Tests the Process function on a MacOS Document Versions file."""
    plugin = macos_document_versions.MacOSDocumentVersionsPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['document_versions.sql'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'creation_time': '2014-01-21T02:03:00+00:00',
        'data_type': 'macos:document_versions:file',
        'name': 'Spain is beautiful.rtf',
        'last_seen_time': '2014-01-21T02:13:01+00:00',
        'path': '/Users/moxilo/Documents',
        'user_sid': '501',
        'version_path': (
            '/.DocumentRevisions-V100/PerUID/501/1/com.apple.documentVersions/'
            '08CFEB5A-5CDA-486F-AED5-EA35BF3EE4C2.rtf')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
