#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Kik messenger plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import kik_ios

from tests.parsers.sqlite_plugins import test_lib


class KikMessageTest(test_lib.SQLitePluginTestCase):
  """Tests for the Kik message database plugin."""

  def testProcess(self):
    """Test the Process function on a Kik messenger kik.sqlite file."""
    plugin = kik_ios.KikIOSPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['kik_ios.sqlite'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 60)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'body': 'Hello',
        'data_type': 'ios:kik:messaging',
        'date_time': '2015-06-29 12:26:11.000000',
        'displayname': 'Ken Doh',
        'message_status': 94,
        'message_type': 2,
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'username': 'ken.doh'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
