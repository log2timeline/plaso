#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the xchatscrollback log parser."""

import unittest

from dfvfs.file_io import fake_file_io
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context as dfvfs_context

from plaso.parsers import text_parser
from plaso.parsers.text_plugins import xchatscrollback

from tests.parsers.text_plugins import test_lib


class XChatScrollbackLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the xchatscrollback log parser."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat method."""
    plugin = xchatscrollback.XChatScrollbackLogTextPlugin()

    resolver_context = dfvfs_context.Context()
    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')

    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, (
        b'T 1232315916 Python interface unloaded\n'))
    file_object.Open()

    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(None, text_reader)
    self.assertTrue(result)

    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, (
        b'T1232315916 Python interface unloaded\n'))
    file_object.Open()

    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(None, text_reader)
    self.assertFalse(result)

    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, (
        b'T 1232315916Python interface unloaded\n'))
    file_object.Open()

    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(None, text_reader)
    self.assertFalse(result)

    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, (
        b'T 12323159160 Python interface unloaded\n'))
    file_object.Open()

    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(None, text_reader)
    self.assertFalse(result)

    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, (
        b'.TH MT 1 \" -*- nroff -*-\n'))
    file_object.Open()

    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(None, text_reader)
    self.assertFalse(result)

  def testProcess(self):
    """Tests the Process function."""
    plugin = xchatscrollback.XChatScrollbackLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['xchatscrollback.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '2009-01-16T02:56:19+00:00',
        'data_type': 'xchat:scrollback:line',
        'text': '* Speaking now on ##plaso##'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
