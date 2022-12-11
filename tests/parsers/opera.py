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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'opera:history:typed_entry',
        'entry_selection': 'Filled from autocomplete.',
        'last_typed_time': '2013-11-11T23:45:27+00:00',
        'url': 'plaso.kiddaland.net'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class OperaGlobalParserTest(test_lib.ParserTestCase):
  """Tests for the Opera Global History parser."""

  def testParseFile(self):
    """Read a history file and run a few tests."""
    parser = opera.OperaGlobalHistoryParser()
    storage_writer = self._ParseFile(['global_history.dat'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 37)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'opera:history:entry',
        'description': 'First and Only Visit',
        'last_visited_time': '2013-11-11T22:45:46+00:00',
        'title': 'Karl Bretaprins fær ellilífeyri - mbl.is',
        'url': (
            'http://www.mbl.is/frettir/erlent/2013/11/11/'
            'karl_bretaprins_faer_ellilifeyri/')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
