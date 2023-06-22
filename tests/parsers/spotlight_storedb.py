#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple Spotlight store database parser."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.parsers import spotlight_storedb

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class SpotlightStoreDatabaseParserTest(test_lib.ParserTestCase):
  """Tests for the Apple Spotlight store database parser."""

  def testParse(self):
    """Tests the Parse function."""
    test_file_path = os.path.join(
        shared_test_lib.TEST_DATA_PATH, 'spotlight.10.13.dmg')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_MODI, parent=test_path_spec)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GPT, location='/p1',
        parent=test_path_spec)

    test_file_path = (
        '/.Spotlight-V100/Store-V2/D980C3E8-1007-4F67-9911-9143A0B3427A/'
        '.store.db')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_HFS, location=test_file_path,
        parent=test_path_spec)

    parser = spotlight_storedb.SpotlightStoreDatabaseParser()
    storage_writer = self._ParseFileByPathSpec(test_path_spec, parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '2023-06-22T18:34:06.000000+00:00',
        'attribute_change_time': None,
        'content_creation_time': '2023-06-22T18:34:06.000000+00:00',
        'content_modification_time': '2023-06-22T18:34:06.000000+00:00',
        'content_type': 'public.data',
        'creation_time': '2023-06-22T18:34:06.000000+00:00',
        'data_type': 'spotlight:metadata_item',
        'downloaded_time': None,
        'file_name': 'LICENSE',
        'file_system_identifier': 20,
        'kind': 'Unknown document',
        'modification_time': '2023-06-22T18:34:06.000000+00:00',
        'parent_file_system_identifier': 2,
        'purchase_time': None,
        'snapshot_times': None,
        'update_time': '2023-06-22T18:34:08.287881+00:00',
        'used_times': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

  def testParseWithLZ4CompressedPage(self):
    """Tests the Parse function on a file with a LZ4 compressed page."""
    parser = spotlight_storedb.SpotlightStoreDatabaseParser()
    storage_writer = self._ParseFile(['859631-store.db'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1848)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': None,
        'attribute_change_time': None,
        'content_creation_time': None,
        'content_modification_time': None,
        'content_type': None,
        'creation_time': None,
        'data_type': 'spotlight:metadata_item',
        'downloaded_time': None,
        'file_name': None,
        'file_system_identifier': None,
        'kind': None,
        'modification_time': None,
        'purchase_time': None,
        'snapshot_times': None,
        'update_time': '2019-09-17T09:22:07.536585+00:00',
        'used_times': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testParseWithStreamsMap(self):
    """Tests the Parse function on a database that uses a streams map."""
    test_file_path = os.path.join(
        shared_test_lib.TEST_DATA_PATH, 'spotlight.12.dmg')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_MODI, parent=test_path_spec)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GPT, location='/p1',
        parent=test_path_spec)

    test_file_path = (
        '/.Spotlight-V100/Store-V2/B8A60235-5AE9-4A1A-9004-3F40B6FF4C28/'
        '.store.db')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_HFS, location=test_file_path,
        parent=test_path_spec)

    parser = spotlight_storedb.SpotlightStoreDatabaseParser()
    storage_writer = self._ParseFileByPathSpec(test_path_spec, parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '2023-06-20T05:10:24.000000+00:00',
        'attribute_change_time': None,
        'content_creation_time': '2023-06-20T05:10:24.000000+00:00',
        'content_modification_time': '2023-06-20T05:10:24.000000+00:00',
        'content_type': 'public.data',
        'creation_time': '2023-06-20T05:10:24.000000+00:00',
        'data_type': 'spotlight:metadata_item',
        'downloaded_time': None,
        'file_name': 'LICENSE',
        'file_system_identifier': 18,
        'kind': 'Document',
        'modification_time': '2023-06-20T05:10:24.000000+00:00',
        'parent_file_system_identifier': 2,
        'purchase_time': None,
        'snapshot_times': None,
        'update_time': '2023-06-21T03:42:12.717812+00:00',
        'used_times': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
