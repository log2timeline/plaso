#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Opera browser history parsers."""

import unittest

from plaso.parsers import opera

from tests.parsers import test_lib


class OperaTypedParserTest(test_lib.ParserTestCase):
  """Tests for the Opera Typed History parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = opera.OperaTypedHistoryParser()
    storage_writer = self._ParseFile(['typed_history.xml'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'entry_selection': 'Filled from autocomplete.',
        'timestamp': '2013-11-11 23:45:27.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_string = 'plaso.kiddaland.net (Filled from autocomplete.)'

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(event_data, expected_string, expected_string)

    expected_event_values = {
        'entry_selection': 'Manually typed.',
        'timestamp': '2013-11-11 22:46:07.000000'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_string = 'theonion.com (Manually typed.)'

    event_data = self._GetEventDataOfEvent(storage_writer, events[3])
    self._TestGetMessageStrings(event_data, expected_string, expected_string)


class OperaGlobalParserTest(test_lib.ParserTestCase):
  """Tests for the Opera Global History parser."""

  def testParseFile(self):
    """Read a history file and run a few tests."""
    parser = opera.OperaGlobalHistoryParser()
    storage_writer = self._ParseFile(['global_history.dat'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 37)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'timestamp': '2013-11-11 22:45:46.000000'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_message = (
        'http://www.mbl.is/frettir/erlent/2013/11/11/'
        'karl_bretaprins_faer_ellilifeyri/ (Karl Bretaprins fær ellilífeyri'
        ' - mbl.is) [First and Only Visit]')
    expected_short_message = (
        'http://www.mbl.is/frettir/erlent/2013/11/11/'
        'karl_bretaprins_faer_ellilifeyri/...')

    event_data = self._GetEventDataOfEvent(storage_writer, events[4])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2013-11-11 22:45:55.000000'}

    self.CheckEventValues(storage_writer, events[10], expected_event_values)

    expected_event_values = {
        'timestamp': '2013-11-11 22:46:16.000000',
        'title': (
            '10 Celebrities You Never Knew Were Abducted And Murdered '
            'By Andie MacDowell | The Onion - America\'s Finest News Source')}

    self.CheckEventValues(storage_writer, events[16], expected_event_values)


if __name__ == '__main__':
  unittest.main()
