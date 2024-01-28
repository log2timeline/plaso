#!/usr/bin/env python3
# -*- coding: utf-8 -*- #
"""Tests for the bash history text parser plugin."""

import unittest

from dfvfs.helpers import fake_file_system_builder

from plaso.parsers import text_parser
from plaso.parsers.text_plugins import bash_history

from tests.parsers.text_plugins import test_lib


class BashHistoryTextPluginTest(test_lib.TextPluginTestCase):
  """Testd for the bash history text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat method."""
    plugin = bash_history.BashHistoryTextPlugin()

    # Check a bash history file.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'#1380630977\n'
        b'/usr/lib/plaso\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(result)

    # Check a desynchronized bash history file.
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'/sbin/reboot\n'
        b'#1380630977\n'
        b'/usr/lib/plaso\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(result)

  def testProcess(self):
    """Tests the Process function."""
    plugin = bash_history.BashHistoryTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['bash_history'], plugin)

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
        'command': '/usr/lib/plaso',
        'data_type': 'bash:history:entry',
        'written_time': '2013-10-01T12:36:17+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test multi line.
    expected_event_values = {
        'command': (
            'binary argument1 "--params=\\ '
            'param1=foo, param2=bar " argument2'),
        'data_type': 'bash:history:entry',
        'written_time': '2021-06-10T22:30:36+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessWithDesynchronizedFile(self):
    """Tests the Process function with a desynchronized file.

    A desynchronized bash history file will start with the command line instead
    of the timestamp.
    """
    plugin = bash_history.BashHistoryTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['bash_history_desync'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 5)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'command': '/usr/lib/plaso',
        'data_type': 'bash:history:entry',
        'written_time': '2013-10-01T12:36:17+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Test multi line.
    expected_event_values = {
        'command': (
            'binary argument1 "--params=\\ '
            'param1=foo, param2=bar " argument2'),
        'data_type': 'bash:history:entry',
        'written_time': '2021-06-10T22:30:36+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
