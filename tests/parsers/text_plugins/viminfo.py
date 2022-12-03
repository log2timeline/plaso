#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Viminfo text parser plugin."""

import unittest

from plaso.parsers.text_plugins import viminfo
from plaso.containers import warnings

from tests.parsers.text_plugins import test_lib


class ViminfoTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Viminfo text parser plugin."""

  # pylint: disable=protected-access

  def testProcess(self):
    """Tests the Process function."""
    plugin = viminfo.VimInfoTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['.viminfo'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test command line history event data.
    expected_event_values = {
        'data_type': 'viminfo:history',
        'history_type': 'Command Line History',
        'history_value': 'e TEST',
        'item_number': 0,
        'recorded_time': '2009-02-13T23:31:30+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test search string history event data.
    expected_event_values = {
        'data_type': 'viminfo:history',
        'history_type': 'Search String History',
        'history_value': '/test_search',
        'item_number': 0,
        'recorded_time': '2009-02-13T23:31:32+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

    # Test register event data.
    expected_event_values = {
        'data_type': 'viminfo:history',
        'history_type': 'Register',
        'history_value': 'test register',
        'item_number': 0,
        'recorded_time': '2009-02-13T23:31:34+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)

    # Test file mark event data.
    expected_event_values = {
        'data_type': 'viminfo:history',
        'history_type': 'File mark',
        'filename': '~\\_vimrc',
        'item_number': 0,
        'recorded_time': '2009-02-13T23:31:36+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 6)
    self.CheckEventData(event_data, expected_event_values)

    # Test jump list event data.
    expected_event_values = {
        'data_type': 'viminfo:history',
        'history_type': 'Jumplist',
        'filename': '~\\_vimrc',
        'item_number': 0,
        'recorded_time': '2009-02-13T23:31:38+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 8)
    self.CheckEventData(event_data, expected_event_values)

    # The extraction warnings are due to the last 6 lines of the test file.
    # These are the "history marks" which are currently not parsed.
    extraction_warnings = list(storage_writer.GetAttributeContainers(
        warnings.ExtractionWarning.CONTAINER_TYPE))

    expected_message = 'unable to parse log line: 64 "> ~\\_vimrc"'

    self.assertEqual(extraction_warnings[0].message, expected_message)

    expected_message = (
        'unable to parse log line: 68 "> C:\\Program Files (x86)\\Vim\\.vimrc"')

    self.assertEqual(extraction_warnings[3].message, expected_message)


if __name__ == '__main__':
  unittest.main()
