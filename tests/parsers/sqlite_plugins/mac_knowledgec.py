#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS Knowledge C db."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import mac_knowledgec

from tests.parsers.sqlite_plugins import test_lib


class MacKnowledgecTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacOS KnowledgeC database."""

  def testProcessHighSierra(self):
    """Tests the Process function on a MacOS 10.13 database."""
    plugin = mac_knowledgec.MacKnowledgeCPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['mac_knowledgec-10.13.db'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 51)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # TODO: look into rounding difference between date_time and timestamp
    expected_event_values = {
        'bundle_identifier': 'com.apple.Installer-Progress',
        'data_type': 'mac:knowledgec:application',
        'date_time': '2019-02-10 16:59:58.860664',
        'duration': 1,
        'timestamp': '2019-02-10 16:59:58.860665',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testProcessMojave(self):
    """Tests the Process function on a MacOS 10.14 database."""
    plugin = mac_knowledgec.MacKnowledgeCPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['mac_knowledgec-10.14.db'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 231)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'bundle_identifier': 'com.apple.Terminal',
        'data_type': 'mac:knowledgec:application',
        'date_time': '2019-05-08 13:57:30.668998',
        'duration': 1041,
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[225], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:knowledgec:safari',
        'date_time': '2019-05-08 13:57:20.000000',
        'duration': 0,
        'timestamp_desc': definitions.TIME_DESCRIPTION_END,
        'title': 'Instagram',
        'url': 'https://www.instagram.com/'}

    self.CheckEventValues(storage_writer, events[212], expected_event_values)


if __name__ == '__main__':
  unittest.main()
