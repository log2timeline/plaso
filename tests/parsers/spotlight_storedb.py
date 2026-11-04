#!/usr/bin/env python3
"""Tests for the Apple Spotlight store database parser."""

import io
import os
import struct
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.lib import errors
from plaso.parsers import spotlight_storedb

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class SpotlightStoreDatabaseParserTest(test_lib.ParserTestCase):
    """Tests for the Apple Spotlight store database parser."""

    # pylint: disable=protected-access

    def testReadMapPagesWithZeroPageSize(self):
        """Tests the _ReadMapPages function stops on a zero map page size.

        A map page header with a page_size of 0 does not advance the map offset,
        which previously caused _ReadMapPages to loop without terminating.
        """
        # Map page header: signature "1mbd", page_size=0, number_of_map_values=0
        # and two unused uint32 values.
        map_page_data = b"1mbd" + struct.pack("<4I", 0, 0, 0, 0)

        file_object = io.BytesIO(map_page_data)

        parser = spotlight_storedb.SpotlightStoreDatabaseParser()
        parser._map_values = []

        with self.assertRaises(errors.ParseError):
            parser._ReadMapPages(file_object, 0, len(map_page_data))

    def testReadPropertyPagesWithSelfReferencingBlock(self):
        """Tests the _ReadPropertyPages function stops on a self-referencing block.

        A property page whose next block number refers back to the same page
        previously caused _ReadPropertyPages to loop without terminating.
        """
        # Property page header at block 1 (offset 0x1000): signature "2pbd",
        # page_size=32, used_page_size=0, property_table_type=0x41 and an unused
        # uncompressed_page_size, followed by a property values header whose
        # next_block_number refers back to block 1.
        property_page_data = b"2pbd" + struct.pack("<4I", 32, 0, 0x00000041, 0)
        property_page_data += struct.pack("<IQ", 1, 0)

        file_object = io.BytesIO(b"\x00" * 0x1000 + property_page_data)

        parser = spotlight_storedb.SpotlightStoreDatabaseParser()

        with self.assertRaises(errors.ParseError):
            parser._ReadPropertyPages(file_object, 1, {})

    def testParse(self):
        """Tests the Parse function."""
        test_file_path = os.path.join(
            shared_test_lib.TEST_DATA_PATH, "spotlight.10.13.dmg"
        )
        test_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        test_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_MODI, parent=test_path_spec
        )
        test_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_GPT, location="/p1", parent=test_path_spec
        )
        test_file_path = (
            "/.Spotlight-V100/Store-V2/D980C3E8-1007-4F67-9911-9143A0B3427A/"
            ".store.db"
        )
        test_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_HFS,
            location=test_file_path,
            parent=test_path_spec,
        )
        parser = spotlight_storedb.SpotlightStoreDatabaseParser()
        storage_writer = self._ParseFileByPathSpec(test_path_spec, parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 3)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "added_time": "2023-06-22T18:34:06.000000+00:00",
            "attribute_change_time": None,
            "content_creation_time": "2023-06-22T18:34:06.000000+00:00",
            "content_modification_time": "2023-06-22T18:34:06.000000+00:00",
            "content_type": "public.data",
            "creation_time": "2023-06-22T18:34:06.000000+00:00",
            "data_type": "spotlight:metadata_item",
            "downloaded_time": None,
            "file_system_identifier": 20,
            "filename": "LICENSE",
            "kind": "Unknown document",
            "modification_time": "2023-06-22T18:34:06.000000+00:00",
            "parent_file_system_identifier": 2,
            "purchase_time": None,
            "snapshot_times": None,
            "update_time": "2023-06-22T18:34:08.287881+00:00",
            "used_times": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithLZ4CompressedPage(self):
        """Tests the Parse function on a file with a LZ4 compressed page."""
        parser = spotlight_storedb.SpotlightStoreDatabaseParser()
        storage_writer = self._ParseFile(["859631-store.db"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1848)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "added_time": None,
            "attribute_change_time": None,
            "content_creation_time": None,
            "content_modification_time": None,
            "content_type": None,
            "creation_time": None,
            "data_type": "spotlight:metadata_item",
            "downloaded_time": None,
            "file_system_identifier": None,
            "filename": None,
            "kind": None,
            "modification_time": None,
            "purchase_time": None,
            "snapshot_times": None,
            "update_time": "2019-09-17T09:22:07.536585+00:00",
            "used_times": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithStreamsMap(self):
        """Tests the Parse function on a database that uses a streams map."""
        test_file_path = os.path.join(
            shared_test_lib.TEST_DATA_PATH, "spotlight.12.dmg"
        )
        test_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        test_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_MODI, parent=test_path_spec
        )
        test_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_GPT, location="/p1", parent=test_path_spec
        )
        test_file_path = (
            "/.Spotlight-V100/Store-V2/B8A60235-5AE9-4A1A-9004-3F40B6FF4C28/"
            ".store.db"
        )
        test_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_HFS,
            location=test_file_path,
            parent=test_path_spec,
        )
        parser = spotlight_storedb.SpotlightStoreDatabaseParser()
        storage_writer = self._ParseFileByPathSpec(test_path_spec, parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 3)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "added_time": "2023-06-20T05:10:24.000000+00:00",
            "attribute_change_time": None,
            "content_creation_time": "2023-06-20T05:10:24.000000+00:00",
            "content_modification_time": "2023-06-20T05:10:24.000000+00:00",
            "content_type": "public.data",
            "creation_time": "2023-06-20T05:10:24.000000+00:00",
            "data_type": "spotlight:metadata_item",
            "downloaded_time": None,
            "file_system_identifier": 18,
            "filename": "LICENSE",
            "kind": "Document",
            "modification_time": "2023-06-20T05:10:24.000000+00:00",
            "parent_file_system_identifier": 2,
            "purchase_time": None,
            "snapshot_times": None,
            "update_time": "2023-06-21T03:42:12.717812+00:00",
            "used_times": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
