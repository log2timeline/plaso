#!/usr/bin/env python3
# -*_ coding: utf-8 -*-
"""Tests for the Zsh extended_history parser."""

import unittest

from dfvfs.file_io import fake_file_io
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context as dfvfs_context

from plaso.parsers import text_parser
from plaso.parsers import zsh_extended_history

from tests.parsers import test_lib


class ZshExtendedHistoryTest(test_lib.ParserTestCase):
  """Tests for the Zsh extended_history parser."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat method."""
    parser = zsh_extended_history.ZshExtendedHistoryParser()

    resolver_context = dfvfs_context.Context()
    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')

    file_object = fake_file_io.FakeFile(
        resolver_context, test_path_spec, b': 1457771210:0;cd plaso')
    file_object.Open()

    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = parser.CheckRequiredFormat(None, text_reader)
    self.assertTrue(result)

    file_object = fake_file_io.FakeFile(
        resolver_context, test_path_spec, b': 2016-03-26 11:54:53;0;cd plaso')
    file_object.Open()

    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = parser.CheckRequiredFormat(None, text_reader)
    self.assertFalse(result)

  def testParse(self):
    """Tests for the Parse method."""
    parser = zsh_extended_history.ZshExtendedHistoryParser()
    storage_writer = self._ParseFile(['zsh_extended_history.txt'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'command': 'cd plaso',
        'data_type': 'shell:zsh:history',
        'elapsed_seconds': 0,
        'last_written_time': '2016-03-12T08:26:50+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
