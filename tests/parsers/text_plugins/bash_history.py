#!/usr/bin/env python3
# -*- coding: utf-8 -*- #
"""Tests for the bash history text parser plugin."""

import unittest

from plaso.parsers.text_plugins import bash_history

from tests.parsers.text_plugins import test_lib


class BashHistoryTextPluginTest(test_lib.TextPluginTestCase):
  """Testd for the bash history text parser plugin."""

  def _TestEventsFromFile(
      self, storage_writer, expected_number_of_extraction_warnings=0):
    """Validates that all events are as expected.

    Args:
      storage_writer (FakeStorageWriter): storage writer.
      expected_number_of_extraction_warnings (Optional[int]): number of expected
          extraction warnings.
    """
    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, expected_number_of_extraction_warnings)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'command': '/usr/lib/plaso',
        'data_type': 'bash:history:entry',
        'written_time': '2013-10-01T12:36:17+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessWithDesynchronizedFile(self):
    """Tests the Process function with a desynchronized file.

    A desynchronized file is one with half an event at the top. That is, it
    starts with a command line instead of a timestamp.
    """
    plugin = bash_history.BashHistoryTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['bash_history_desync'], plugin)

    self._TestEventsFromFile(
        storage_writer, expected_number_of_extraction_warnings=1)

  def testProcessWithSynchronizedFile(self):
    """Tests the Process function with a synchronized file.

    A synchronized file is one that starts with a timestamp line.
    """
    plugin = bash_history.BashHistoryTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['bash_history'], plugin)

    self._TestEventsFromFile(storage_writer)


if __name__ == '__main__':
  unittest.main()
