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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 30)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'chrome:preferences:extensions_autoupdater',
        'message': 'Chrome extensions autoupdater last run',
        'timestamp': '2014-11-12 13:01:43.926143'}

    self.CheckEventValues(storage_writer, events[17], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:extensions_autoupdater',
        'message': 'Chrome extensions autoupdater next run',
        'timestamp': '2014-11-12 18:20:21.519200'}

    self.CheckEventValues(storage_writer, events[18], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:extensions_autoupdater',
        'message': 'Chrome history was cleared by user',
        'timestamp': '2016-06-08 16:17:47.453766'}

    self.CheckEventValues(storage_writer, events[22], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:extension_installation',
        'extension_id': 'mgndgikekgjfcpckkfioiadnlibdjbkf',
        'extension_name': 'Chrome',
        'path': (
            'C:\\Program Files\\Google\\Chrome\\Application\\38.0.2125.111\\'
            'resources\\chrome_app'),
        'timestamp': '2014-11-05 18:31:24.154837'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:content_settings:exceptions',
        'permission': 'geolocation',
        'primary_url': '',
        'timestamp': '2016-11-14 14:12:50.588974'}

    self.CheckEventValues(storage_writer, events[25], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:content_settings:exceptions',
        'permission': 'midi_sysex',
        'primary_url': 'https://rawgit.com:443',
        'timestamp': '2016-11-11 16:20:09.866137'}

    self.CheckEventValues(storage_writer, events[23], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:content_settings:exceptions',
        'permission': 'notifications',
        'primary_url': 'https://rawgit.com:443',
        'timestamp': '2016-11-14 14:13:00.639332'}

    self.CheckEventValues(storage_writer, events[29], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:content_settings:exceptions',
        'permission': 'notifications',
        'primary_url': 'https://rawgit.com:443',
        'timestamp': '2016-11-14 14:13:00.627093'}

    self.CheckEventValues(storage_writer, events[28], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:content_settings:exceptions',
        'permission': 'media_stream_mic',
        'primary_url': '',
        'timestamp': '2016-11-14 14:12:54.899474'}

    self.CheckEventValues(storage_writer, events[27], expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:preferences:content_settings:exceptions',
        'permission': 'media_stream_mic',
        'primary_url': 'https://rawgit.com:443',
        'timestamp': '2016-11-14 14:12:53.667838'}

    self.CheckEventValues(storage_writer, events[26], expected_event_values)


if __name__ == '__main__':
  unittest.main()
