#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS Duet/KnowledgeC database."""

import unittest

from plaso.parsers.sqlite_plugins import macos_knowledgec

from tests.parsers.sqlite_plugins import test_lib


class MacOSKnowledgecTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacOS Duet/KnowledgeC database."""

  def testProcessHighSierra(self):
    """Tests the Process function on a MacOS 10.13 database."""
    plugin = macos_knowledgec.MacOSKnowledgeCPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['mac_knowledgec-10.13.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 17)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'bundle_identifier': 'com.apple.Installer-Progress',
        'creation_time': '2019-02-10T16:59:58.860664+00:00',
        'data_type': 'macos:knowledgec:application',
        'duration': 1,
        'end_time': '2019-02-10T16:59:58.000000+00:00',
        'start_time': '2019-02-10T16:59:57.000000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessMojave(self):
    """Tests the Process function on a MacOS 10.14 database."""
    plugin = macos_knowledgec.MacOSKnowledgeCPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['mac_knowledgec-10.14.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 77)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'bundle_identifier': 'com.apple.Terminal',
        'creation_time': '2019-05-08T13:57:30.668998+00:00',
        'data_type': 'macos:knowledgec:application',
        'duration': 1041,
        'end_time': '2019-05-08T13:57:30.000000+00:00',
        'start_time': '2019-05-08T13:40:09.000000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 75)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'creation_time': '2019-05-08T13:57:20.626870+00:00',
        'data_type': 'macos:knowledgec:safari',
        'duration': 0,
        'end_time': '2019-05-08T13:57:20.000000+00:00',
        'start_time': '2019-05-08T13:57:20.000000+00:00',
        'title': 'Instagram',
        'url': 'https://www.instagram.com/'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 70)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
