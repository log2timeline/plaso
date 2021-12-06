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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'opera:history:typed_entry',
        'date_time': '2013-11-11 23:45:27',
        'entry_selection': 'Filled from autocomplete.',
        'url': 'plaso.kiddaland.net'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'opera:history:typed_entry',
        'date_time': '2013-11-11 22:46:07',
        'entry_selection': 'Manually typed.',
        'url': 'theonion.com'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)


class OperaGlobalParserTest(test_lib.ParserTestCase):
  """Tests for the Opera Global History parser."""

  def testParseFile(self):
    """Read a history file and run a few tests."""
    parser = opera.OperaGlobalHistoryParser()
    storage_writer = self._ParseFile(['global_history.dat'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 37)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'opera:history:entry',
        'date_time': '2013-11-11 22:45:46',
        'description': 'First and Only Visit',
        'title': 'Karl Bretaprins fær ellilífeyri - mbl.is',
        'url': (
            'http://www.mbl.is/frettir/erlent/2013/11/11/'
            'karl_bretaprins_faer_ellilifeyri/')}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'data_type': 'opera:history:entry',
        'date_time': '2013-11-11 22:45:55'}

    self.CheckEventValues(storage_writer, events[10], expected_event_values)

    expected_event_values = {
        'data_type': 'opera:history:entry',
        'date_time': '2013-11-11 22:46:16',
        'title': (
            '10 Celebrities You Never Knew Were Abducted And Murdered '
            'By Andie MacDowell | The Onion - America\'s Finest News Source')}

    self.CheckEventValues(storage_writer, events[16], expected_event_values)


if __name__ == '__main__':
  unittest.main()
