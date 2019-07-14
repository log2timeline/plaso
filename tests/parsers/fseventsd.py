#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for fseventsd file parser."""

from __future__ import unicode_literals

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.formatters import fseventsd as _  # pylint: disable=unused-import
from plaso.parsers import fseventsd

from tests.parsers import test_lib


class FSEventsdParserTest(test_lib.ParserTestCase):
  """Tests for the fseventsd parser."""

  def testParseV1(self):
    """Tests the Parse function on a version 1 file."""
    parser = fseventsd.FseventsdParser()

    path = self._GetTestFilePath(['fsevents-0000000002d89b58'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=path)

    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)

    storage_writer = self._ParseFileByPathSpec(gzip_path_spec, parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 12)

    events = list(storage_writer.GetEvents())

    event = events[3]

    # Do not check the timestamp since it is derived from the file entry.

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.path, '.Spotlight-V100/Store-V1')
    self.assertEqual(event_data.event_identifier, 47747061)
    self.assertEqual(event_data.flags, 0x01000080)

    os_file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)
    expected_time = os_file_entry.modification_time
    expected_timestamp = expected_time.GetPlasoTimestamp()
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        '.Spotlight-V100/Store-V1 '
        'Flag Values: DirectoryCreated, IsDirectory '
        'Flags: 0x01000080 Event Identifier: 47747061')
    expected_short_message = (
        '.Spotlight-V100/Store-V1 DirectoryCreated, IsDirectory')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testParseV2(self):
    """Tests the Parse function on a version 2 file."""
    parser = fseventsd.FseventsdParser()

    path = self._GetTestFilePath(['fsevents-00000000001a0b79'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=path)

    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)

    storage_writer = self._ParseFileByPathSpec(gzip_path_spec, parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    event = events[2]

    # Do not check the timestamp since it is derived from the file entry.

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.path, 'Hi, Sierra')
    self.assertEqual(event_data.event_identifier, 1706838)
    self.assertEqual(event_data.flags, 0x01000008)

    os_file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)
    expected_time = os_file_entry.modification_time
    expected_timestamp = expected_time.GetPlasoTimestamp()
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        'Hi, Sierra Flag Values: Renamed, IsDirectory '
        'Flags: 0x01000008 '
        'Event Identifier: 1706838')
    expected_short_message = 'Hi, Sierra Renamed, IsDirectory'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
