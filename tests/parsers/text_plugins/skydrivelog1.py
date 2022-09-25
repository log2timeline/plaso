#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SkyDrive version 1 log files text parser plugin."""

import unittest

from plaso.parsers.text_plugins import skydrivelog1

from tests.parsers.text_plugins import test_lib


class SkyDriveLog1TextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the SkyDrive version 1 log files text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = skydrivelog1.SkyDriveLog1TextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['skydrive_v1.log'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 18)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'skydrive:log:old:line',
        'date_time': '2013-08-01T21:22:28.999+00:00',
        'log_level': 'DETAIL',
        'source_code': 'global.cpp:626!logVersionInfo',
        'text': '17.0.2011.0627 (Ship)'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'skydrive:log:old:line',
        'date_time': '2013-08-01T21:22:29.702+00:00'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'skydrive:log:old:line',
        'date_time': '2013-08-01T21:22:29.702+00:00'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'data_type': 'skydrive:log:old:line',
        'date_time': '2013-08-01T21:22:29.702+00:00',
        'text': (
            'SyncToken = LM%3d12345678905670%3bID%3d1234567890E059C0!'
            '103%3bLR%3d12345678905623%3aEP%3d2')}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'data_type': 'skydrive:log:old:line',
        'date_time': '2013-08-01T21:22:58.344+00:00'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'data_type': 'skydrive:log:old:line',
        'date_time': '2013-08-01T21:22:58.344+00:00'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'data_type': 'skydrive:log:old:line',
        'date_time': '2013-08-01T21:28:46.742+00:00',
        'text': 'SyncToken = Not a sync token (\xe0\xe8\xec\xf2\xf9)!'}

    self.CheckEventValues(storage_writer, events[17], expected_event_values)


if __name__ == '__main__':
  unittest.main()
