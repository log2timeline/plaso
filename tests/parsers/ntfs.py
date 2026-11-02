#!/usr/bin/env python3
"""Tests for the NTFS metadata file parser."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.lib import errors
from plaso.parsers import ntfs

from tests.parsers import test_lib


class TestMFTEntry:
    """MFT entry for testing.

    Attributes:
      file_reference (int): NTFS file reference.
    """

    def __init__(self, file_reference):
        """Initializes an MFT entry for testing.

        Args:
          file_reference (int): NTFS file reference.
        """
        super().__init__()
        self.file_reference = file_reference


class TestMFTAttribute:
    """MFT attribute for testing.

    Attributes:
      attribute_type (int): attribute type.
      birth_droid_file_identifier (str): birth droid file identifier.
      droid_file_identifier (str): droid file identifier.
    """

    def __init__(
        self, attribute_type, droid_file_identifier, birth_droid_file_identifier
    ):
        """Initializes an MFT attribute for testing.

        Args:
          attribute_type (int): attribute type.
          droid_file_identifier (str): droid file identifier.
          birth_droid_file_identifier (str): birth droid file identifier.
        """
        super().__init__()
        self.attribute_type = attribute_type
        self.droid_file_identifier = droid_file_identifier
        self.birth_droid_file_identifier = birth_droid_file_identifier


class NTFSMFTParserTest(test_lib.ParserTestCase):
    """Tests for NTFS $MFT metadata file parser."""

    # pylint: disable=protected-access

    def testParseFile(self):
        """Tests the Parse function on a stand-alone $MFT file."""
        parser = ntfs.NTFSMFTParser()

        test_file_path = self._GetTestFilePath(["MFT"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )

        storage_writer = self._ParseFileByPathSpec(os_path_spec, parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 31642)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Test path hints of a regular file.
        expected_event_values = {
            "access_time": "2007-06-30T12:58:50.2740544+00:00",
            "creation_time": "2007-06-30T12:58:50.2740544+00:00",
            "data_type": "fs:stat:ntfs",
            "entry_modification_time": "2007-06-30T12:58:50.2740544+00:00",
            "modification_time": "2007-06-30T12:58:50.2740544+00:00",
            "name": "SAM",
            "path_hints": ["\\WINDOWS\\system32\\config\\SAM"],
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 7204)
        self.CheckEventData(event_data, expected_event_values)

        # Test path hints of a deleted file.
        expected_path_hints = [
            (
                "\\Documents and Settings\\Donald Blake\\Local Settings\\"
                "Temporary Internet Files\\Content.IE5\\9EUWFPZ1\\CAJA1S19.js"
            )
        ]

        expected_event_values = {
            "access_time": "2009-01-14T03:38:58.5869993+00:00",
            "creation_time": "2009-01-14T03:38:58.5869993+00:00",
            "data_type": "fs:stat:ntfs",
            "entry_modification_time": "2009-01-14T03:38:58.5869993+00:00",
            "is_allocated": False,
            "modification_time": "2009-01-14T03:38:58.5869993+00:00",
            "name": "CAJA1S19.js",
            "path_hints": expected_path_hints,
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 30173)
        self.CheckEventData(event_data, expected_event_values)

        # Testing path hint of orphaned file.
        expected_event_values = {
            "access_time": "2009-01-14T21:07:11.5721856+00:00",
            "creation_time": "2009-01-14T21:07:11.5721856+00:00",
            "data_type": "fs:stat:ntfs",
            "entry_modification_time": "2009-01-14T21:07:11.5721856+00:00",
            "is_allocated": False,
            "modification_time": "2009-01-14T21:07:11.5721856+00:00",
            "name": "menu.text.css",
            "path_hints": ["$Orphan\\session\\menu.text.css"],
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 31412)
        self.CheckEventData(event_data, expected_event_values)

        # Test distributed link tracking event data.
        expected_event_values = {
            "creation_time": "2007-06-30T12:58:40.5000041+00:00",
            "data_type": "windows:distributed_link_tracking:creation",
            "mac_address": "db:30:99:be:ae:3c",
            "origin": "$MFT: 462-1",
            "uuid": "9fe44b69-2709-11dc-a06b-db3099beae3c",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 920)
        self.CheckEventData(event_data, expected_event_values)

    def testParseObjectIDAttribute(self):
        """Tests the _ParseObjectIDAttribute function."""
        parser = ntfs.NTFSMFTParser()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        mft_entry = TestMFTEntry((1 << 48) | 462)
        mft_attribute = TestMFTAttribute(
            0x00000040,
            "9fe44b69-2709-11dc-a06b-db3099beae3c",
            "9fe44b71-2709-11dc-a06b-001122334455",
        )

        parser._ParseObjectIDAttribute(parser_mediator, mft_entry, mft_attribute)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "windows:distributed_link_tracking:creation",
            "mac_address": "db:30:99:be:ae:3c",
            "origin": "$MFT: 462-1",
            "uuid": "9fe44b69-2709-11dc-a06b-db3099beae3c",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "windows:distributed_link_tracking:creation",
            "mac_address": "00:11:22:33:44:55",
            "origin": "$MFT: 462-1",
            "uuid": "9fe44b71-2709-11dc-a06b-001122334455",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

    def testParseImage(self):
        """Tests the Parse function on a storage media image."""
        parser = ntfs.NTFSMFTParser()

        test_file_path = self._GetTestFilePath(["vsstest.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec
        )
        tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=0,
            location="/$MFT",
            parent=qcow_path_spec,
        )

        storage_writer = self._ParseFileByPathSpec(tsk_path_spec, parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 71)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "access_time": "2013-12-03T06:30:41.8079077+00:00",
            "attribute_type": 0x00000030,
            "creation_time": "2013-12-03T06:30:41.8079077+00:00",
            "data_type": "fs:stat:ntfs",
            "entry_modification_time": "2013-12-03T06:30:41.8079077+00:00",
            "file_reference": 0x1000000000000,
            "is_allocated": True,
            "modification_time": "2013-12-03T06:30:41.8079077+00:00",
            "name": "$MFT",
            "parent_file_reference": 0x5000000000005,
            "path_hints": ["\\$MFT"],
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Note that the source file is a RAW (VMDK flat) image.
        test_file_path = self._GetTestFilePath(["multi_partition_image.vmdk"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        p2_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
            location="/p2",
            part_index=3,
            start_offset=0x00510000,
            parent=os_path_spec,
        )
        tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=0,
            location="/$MFT",
            parent=p2_path_spec,
        )

        storage_writer = self._ParseFileByPathSpec(tsk_path_spec, parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 46)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "access_time": "2015-05-15T01:00:26.8925979+00:00",
            "attribute_type": 0x00000030,
            "creation_time": "2015-05-15T01:00:26.8925979+00:00",
            "data_type": "fs:stat:ntfs",
            "entry_modification_time": "2015-05-15T01:00:26.8925979+00:00",
            "file_reference": 0x1000000000000,
            "is_allocated": True,
            "modification_time": "2015-05-15T01:00:26.8925979+00:00",
            "name": "$MFT",
            "parent_file_reference": 0x5000000000005,
            "path_hints": ["\\$MFT"],
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


class NTFSUsnJrnlParser(test_lib.ParserTestCase):
    """Tests for NTFS $UsnJrnl metadata file parser."""

    def testParseImage(self):
        """Tests the Parse function on a storage media image."""
        parser = ntfs.NTFSUsnJrnlParser()

        test_file_path = self._GetTestFilePath(["usnjrnl.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec
        )
        volume_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
            location="/p1",
            part_index=2,
            start_offset=0x00007E00,
            parent=qcow_path_spec,
        )

        # To be able to ignore the sparse data ranges the UsnJrnl parser
        # requires to read directly from the volume.
        storage_writer = self._ParseFileByPathSpec(volume_path_spec, parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 19)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "fs:ntfs:usn_change",
            "filename": "Nieuw - Tekstdocument.txt",
            "file_reference": 0x100000000001E,
            "parent_file_reference": 0x5000000000005,
            "update_reason_flags": 0x00000100,
            "update_time": "2015-11-30T21:15:27.2031250+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def _ReadTestFileData(self, path_segments):
        """Reads the data of a test file.

        Args:
          path_segments (list[str]): path segments inside the test data directory.

        Returns:
          bytes: data of the test file.
        """
        test_file_path = self._GetTestFilePath(path_segments)
        self._SkipIfPathNotExists(test_file_path)

        with open(test_file_path, "rb") as file_object:
            return file_object.read()

    def testParseExportedDataStream(self):
        """Tests the Parse function on an exported $UsnJrnl:$J data stream."""
        parser = ntfs.NTFSUsnJrnlParser()
        storage_writer = self._ParseFile(["UsnJrnl.raw"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 19)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "fs:ntfs:usn_change",
            "filename": "Nieuw - Tekstdocument.txt",
            "file_reference": 0x100000000001E,
            "offset": 0,
            "parent_file_reference": 0x5000000000005,
            "update_reason_flags": 0x00000100,
            "update_time": "2015-11-30T21:15:27.2031250+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testParseExportedDataStreamWithSparseRanges(self):
        """Tests the Parse function on an exported data stream with sparse ranges."""
        parser = ntfs.NTFSUsnJrnlParser()

        usn_records_data = self._ReadTestFileData(["UsnJrnl.raw"])

        # A sparse range of an exported $UsnJrnl:$J data stream is stored as
        # a zero-byte filled range.
        test_data = b"".join(
            [bytes(0x22000), usn_records_data, bytes(0x1000 - len(usn_records_data))]
        )
        file_object = self._CreateFileObject("UsnJrnl.raw", test_data)

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        parser.Parse(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 19)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, {"offset": 0x22000})

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 18)
        self.CheckEventData(event_data, {"offset": 0x22680})

        # Test with an unsupported USN record after the supported USN records.
        unsupported_usn_record_data = b"".join(
            [b"\x40\x00\x00\x00\x03\x00\x00\x00", bytes(56)]
        )
        test_data = b"".join([usn_records_data, unsupported_usn_record_data])
        file_object = self._CreateFileObject("UsnJrnl.raw", test_data)

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        parser.Parse(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 19)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

    def testParseExportedDataStreamWithNearMisses(self):
        """Tests the Parse function on data that is not a $UsnJrnl:$J data stream."""
        parser = ntfs.NTFSUsnJrnlParser()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        # Test with a NTFS $MFT metadata file.
        test_data = self._ReadTestFileData(["MFT"])
        file_object = self._CreateFileObject("MFT", test_data)

        with self.assertRaises(errors.WrongParser):
            parser.Parse(parser_mediator, file_object)

        # Test with text data.
        test_data = b"".join([b"This is not an USN change journal.\n", bytes(64)])
        file_object = self._CreateFileObject("UsnJrnl.raw", test_data)

        with self.assertRaises(errors.WrongParser):
            parser.Parse(parser_mediator, file_object)

        usn_records_data = self._ReadTestFileData(["UsnJrnl.raw"])

        # Test with an unsupported major version.
        test_data = b"".join([usn_records_data[:4], b"\x03\x00", usn_records_data[6:]])
        file_object = self._CreateFileObject("UsnJrnl.raw", test_data)

        with self.assertRaises(errors.WrongParser):
            parser.Parse(parser_mediator, file_object)

        # Test with a record size that is not a multiple of 8.
        test_data = b"".join([b"\x71\x00\x00\x00", usn_records_data[4:]])
        file_object = self._CreateFileObject("UsnJrnl.raw", test_data)

        with self.assertRaises(errors.WrongParser):
            parser.Parse(parser_mediator, file_object)

        # Test with a record size that exceeds the data.
        test_data = usn_records_data[:100]
        file_object = self._CreateFileObject("UsnJrnl.raw", test_data)

        with self.assertRaises(errors.WrongParser):
            parser.Parse(parser_mediator, file_object)

        # Test with a zero record size and a non-zero major version.
        test_data = b"".join([bytes(8), b"\x00\x00\x00\x00\x02\x00\x00\x00", bytes(56)])
        file_object = self._CreateFileObject("UsnJrnl.raw", test_data)

        with self.assertRaises(errors.WrongParser):
            parser.Parse(parser_mediator, file_object)

        # Test with zero-byte filled data only.
        file_object = self._CreateFileObject("UsnJrnl.raw", bytes(0x1000))

        parser.Parse(parser_mediator, file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)


if __name__ == "__main__":
    unittest.main()
