#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Sophos Anti-Virus log (SAV.txt) text parser plugin."""

import unittest

from plaso.parsers.text_plugins import sophos_av

from tests.parsers.text_plugins import test_lib


class SophosAVLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Sophos Anti-Virus log (SAV.txt) text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = sophos_av.SophosAVLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['sav.txt'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'sophos:av:log',
        'date_time': '2010-07-20T18:38:14',
        'text': (
            'File "C:\\Documents and Settings\\Administrator\\Desktop\\'
            'sxl_test_50.com" belongs to virus/spyware \'LiveProtectTest\'.'),
        'timestamp': '2010-07-20 18:38:14.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testProcessWithTimeZone(self):
    """Tests the Process function with a time zone."""
    plugin = sophos_av.SophosAVLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['sav.txt'], plugin, timezone='CET')

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'sophos:av:log',
        'date_time': '2010-07-20T18:38:14',
        'text': (
            'File "C:\\Documents and Settings\\Administrator\\Desktop\\'
            'sxl_test_50.com" belongs to virus/spyware \'LiveProtectTest\'.'),
        'timestamp': '2010-07-20 16:38:14.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
