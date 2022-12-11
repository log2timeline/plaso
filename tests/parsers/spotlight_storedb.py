#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple Spotlight store database parser."""

import unittest

from plaso.parsers import spotlight_storedb

from tests.parsers import test_lib


class SpotlightStoreDatabaseParserTest(test_lib.ParserTestCase):
  """Tests for the Apple Spotlight store database parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = spotlight_storedb.SpotlightStoreDatabaseParser()
    storage_writer = self._ParseFile(['store.db'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 193192)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '2013-06-04T20:53:10.000000+00:00',
        'attribute_change_time': None,
        'content_creation_time': '2009-08-23T23:24:01.000000+00:00',
        'content_modification_time': '2013-06-04T20:53:10.000000+00:00',
        'content_type': 'com.apple.icns',
        'creation_time': '2009-08-23T23:24:01.000000+00:00',
        'data_type': 'spotlight:metadata_item',
        'downloaded_time': None,
        'file_name': 'CIJCanoScan9000F.icns',
        'file_system_identifier': 41322,
        'kind': 'Apple icon image',
        'modification_time': '2013-06-04T20:53:10.000000+00:00',
        'parent_file_system_identifier': 41320,
        'purchase_time': None,
        'snapshot_times': None,
        'update_time': '2015-09-19T18:06:32.552596+00:00',
        'used_times': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

  def testParseLZ4CompressedPage(self):
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


if __name__ == '__main__':
  unittest.main()
