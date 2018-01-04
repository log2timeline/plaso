# -*- coding: utf-8 -*-
"""Tests for fseventsd file parser."""

from __future__ import unicode_literals
import unittest

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib
from plaso.parsers import fseventsd

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver


class FSEventsdParserTest(test_lib.ParserTestCase):
  """Tests for the fseventsd parser."""


  @shared_test_lib.skipUnlessHasTestFile(['fsevents-0000000002d89b58'])
  def testParseV1(self):
    """Tests the Parse function."""
    parser = fseventsd.FseventsdParserV1()

    path = self._GetTestFilePath(['fsevents-0000000002d89b58'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=path)

    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)

    storage_writer = self._ParseFileByPathSpec(gzip_path_spec, parser)

    self.assertEqual(storage_writer.number_of_events, 12)

    events = list(storage_writer.GetEvents())

    event = events[3]
    self.assertEqual(event.path, '.Spotlight-V100/Store-V1')
    self.assertEqual(event.event_id, 47747061)
    self.assertEqual(event.flags, b'\x00\x00\x00\x00\x80\x00\x00\x01')

    os_file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)
    expected_time = os_file_entry.modification_time
    expected_timestamp = expected_time.GetPlasoTimestamp()
    self.assertEqual(event.timestamp, expected_timestamp)

  @shared_test_lib.skipUnlessHasTestFile(['fsevents-00000000001a0b79'])
  def testParseV2(self):
    """Tests the Parse function."""
    parser = fseventsd.FseventsdParserV2()

    path = self._GetTestFilePath(['fsevents-00000000001a0b79'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=path)

    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)

    storage_writer = self._ParseFileByPathSpec(gzip_path_spec, parser)

    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    event = events[2]
    self.assertEqual(event.path, 'Hi, Sierra')
    self.assertEqual(event.event_id, 1706838)
    self.assertEqual(event.flags, b'\x00\x00\x00\x00\x08\x00\x00\x01')

    os_file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)
    expected_time = os_file_entry.modification_time
    expected_timestamp = expected_time.GetPlasoTimestamp()
    self.assertEqual(event.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
