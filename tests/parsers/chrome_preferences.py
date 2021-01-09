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
        'timestamp': '2014-11-12 13:01:43.926143'}

    self.CheckEventValues(storage_writer, events[17], expected_event_values)

    expected_message = 'Chrome extensions autoupdater last run'
    expected_short_message = 'Chrome extensions autoupdater last run'

    event_data = self._GetEventDataOfEvent(storage_writer, events[17])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2014-11-12 18:20:21.519200'}

    self.CheckEventValues(storage_writer, events[18], expected_event_values)

    expected_message = 'Chrome extensions autoupdater next run'
    expected_short_message = 'Chrome extensions autoupdater next run'

    event_data = self._GetEventDataOfEvent(storage_writer, events[18])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2016-06-08 16:17:47.453766'}

    self.CheckEventValues(storage_writer, events[22], expected_event_values)

    expected_message = 'Chrome history was cleared by user'
    expected_short_message = 'Chrome history was cleared by user'

    event_data = self._GetEventDataOfEvent(storage_writer, events[22])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_path = (
        'C:\\Program Files\\Google\\Chrome\\Application\\38.0.2125.111\\'
        'resources\\chrome_app')

    expected_event_values = {
        'data_type': 'chrome:preferences:extension_installation',
        'extension_id': 'mgndgikekgjfcpckkfioiadnlibdjbkf',
        'extension_name': 'Chrome',
        'path': expected_path,
        'timestamp': '2014-11-05 18:31:24.154837'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_message = (
        'CRX ID: mgndgikekgjfcpckkfioiadnlibdjbkf '
        'CRX Name: Chrome '
        'Path: {0:s}'.format(expected_path))
    expected_short_message = (
        'mgndgikekgjfcpckkfioiadnlibdjbkf '
        'C:\\Program Files\\Google\\Chrome\\Application\\3...')

    event_data = self._GetEventDataOfEvent(storage_writer, events[6])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2016-11-14 14:12:50.588974'}

    self.CheckEventValues(storage_writer, events[25], expected_event_values)

    expected_message = 'Permission geolocation used by local file'

    event_data = self._GetEventDataOfEvent(storage_writer, events[25])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    expected_event_values = {
        'timestamp': '2016-11-11 16:20:09.866137'}

    self.CheckEventValues(storage_writer, events[23], expected_event_values)

    expected_message = (
        'Permission midi_sysex used by https://rawgit.com:443')

    event_data = self._GetEventDataOfEvent(storage_writer, events[23])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    expected_event_values = {
        'timestamp': '2016-11-14 14:13:00.639332'}

    self.CheckEventValues(storage_writer, events[29], expected_event_values)

    expected_message = (
        'Permission notifications used by https://rawgit.com:443')
    expected_short_message = (
        'Permission notifications used by https://rawgit.com:443')

    event_data = self._GetEventDataOfEvent(storage_writer, events[29])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2016-11-14 14:13:00.627093'}

    self.CheckEventValues(storage_writer, events[28], expected_event_values)

    expected_message = (
        'Permission notifications used by https://rawgit.com:443')

    event_data = self._GetEventDataOfEvent(storage_writer, events[28])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    expected_event_values = {
        'timestamp': '2016-11-14 14:12:54.899474'}

    self.CheckEventValues(storage_writer, events[27], expected_event_values)

    expected_message = (
        'Permission media_stream_mic used by local file')

    event_data = self._GetEventDataOfEvent(storage_writer, events[27])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    expected_event_values = {
        'timestamp': '2016-11-14 14:12:53.667838'}

    self.CheckEventValues(storage_writer, events[26], expected_event_values)

    expected_message = (
        'Permission media_stream_mic used by https://rawgit.com:443')

    event_data = self._GetEventDataOfEvent(storage_writer, events[26])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
