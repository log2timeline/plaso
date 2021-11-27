#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Chrome Preferences file parser."""

import unittest

from plaso.parsers import chrome_preferences

from tests.parsers import test_lib


class ChromePreferencesParserTest(test_lib.ParserTestCase):
  """Tests for the Google Chrome Preferences file parser."""

  def testParseFile(self):
    """Tests parsing a default profile Preferences file."""
    parser = chrome_preferences.ChromePreferencesParser()
    storage_writer = self._ParseFile(['Preferences'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 30)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'chrome:preferences:extensions_autoupdater',
        'date_time': '2014-11-12 13:01:43.926143',
        'message': 'Chrome extensions autoupdater last run'}

    self.CheckEventValues(storage_writer, events[17], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:extensions_autoupdater',
        'date_time': '2014-11-12 18:20:21.519200',
        'message': 'Chrome extensions autoupdater next run'}

    self.CheckEventValues(storage_writer, events[18], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:extensions_autoupdater',
        'date_time': '2016-06-08 16:17:47.453766',
        'message': 'Chrome history was cleared by user'}

    self.CheckEventValues(storage_writer, events[22], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:extension_installation',
        'date_time': '2014-11-05 18:31:24.154837',
        'extension_id': 'mgndgikekgjfcpckkfioiadnlibdjbkf',
        'extension_name': 'Chrome',
        'path': (
            'C:\\Program Files\\Google\\Chrome\\Application\\38.0.2125.111\\'
            'resources\\chrome_app')}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:content_settings:exceptions',
        'date_time': '2016-11-14 14:12:50.588974',
        'permission': 'geolocation',
        'primary_url': ''}

    self.CheckEventValues(storage_writer, events[25], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:content_settings:exceptions',
        'date_time': '2016-11-11 16:20:09.866137',
        'permission': 'midi_sysex',
        'primary_url': 'https://rawgit.com:443'}

    self.CheckEventValues(storage_writer, events[23], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:content_settings:exceptions',
        'date_time': '2016-11-14 14:13:00.639332',
        'permission': 'notifications',
        'primary_url': 'https://rawgit.com:443'}

    self.CheckEventValues(storage_writer, events[29], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:content_settings:exceptions',
        'date_time': '2016-11-14 14:13:00.627093',
        'permission': 'notifications',
        'primary_url': 'https://rawgit.com:443'}

    self.CheckEventValues(storage_writer, events[28], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:content_settings:exceptions',
        'date_time': '2016-11-14 14:12:54.899474',
        'permission': 'media_stream_mic',
        'primary_url': ''}

    self.CheckEventValues(storage_writer, events[27], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:content_settings:exceptions',
        'date_time': '2016-11-14 14:12:53.667838',
        'permission': 'media_stream_mic',
        'primary_url': 'https://rawgit.com:443'}

    self.CheckEventValues(storage_writer, events[26], expected_event_values)


if __name__ == '__main__':
  unittest.main()
