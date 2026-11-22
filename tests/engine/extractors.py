#!/usr/bin/env python3
"""Tests for the extractor classes."""

import collections
import os
import shutil
import unittest

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import extractors
from plaso.lib import errors
from plaso.parsers import mediator as parsers_mediator

from tests import test_lib as shared_test_lib
from tests.engine import test_lib


class EventDataExtractorTest(test_lib.EngineTestCase):
    """Tests for the event data extractor."""

    # pylint: disable=protected-access

    def _CreateParserMediator(self, storage_writer, file_entry=None):
        """Creates a parser mediator.

        Args:
          storage_writer (StorageWriter): storage writer.
          file_entry (Optional[dfvfs.FileEntry]): file entry object being parsed.

        Returns:
          ParserMediator: parser mediator.
        """
        parser_mediator = parsers_mediator.ParserMediator()
        parser_mediator.SetStorageWriter(storage_writer)

        if file_entry:
            parser_mediator.SetFileEntry(file_entry)

        return parser_mediator

    def _GetTestNTFSFileEntry(self, location, data_stream=None):
        """Retrieves a file entry of the NTFS file system in a test image.

        Args:
          location (str): location of the file entry in the NTFS file system.
          data_stream (Optional[str]): name of the data stream.

        Returns:
          dfvfs.FileEntry: file entry.

        Raises:
          SkipTest: if the path inside the test data directory does not exist and
              the test should be skipped.
        """
        test_file_path = self._GetTestFilePath(["usnjrnl.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=path_spec
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
            location="/p1",
            part_index=2,
            start_offset=0x00007E00,
            parent=path_spec,
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            data_stream=data_stream,
            location=location,
            parent=path_spec,
        )

        return path_spec_resolver.Resolver.OpenFileEntry(path_spec)

    def _GetTestOSFileEntry(self, path_segments):
        """Retrieves a file entry of a test file in the test data directory.

        Args:
          path_segments (list[str]): components of a path to a test file, relative
              to the test_data directory.

        Returns:
          dfvfs.FileEntry: file entry.

        Raises:
          SkipTest: if the path inside the test data directory does not exist and
              the test should be skipped.
        """
        test_file_path = self._GetTestFilePath(path_segments)
        self._SkipIfPathNotExists(test_file_path)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        return path_spec_resolver.Resolver.OpenFileEntry(path_spec)

    def testCheckParserCanProcessFileEntry(self):
        """Tests the _CheckParserCanProcessFileEntry function."""
        test_extractor = extractors.EventDataExtractor(parser_filter_expression="rplog")

        parser = test_extractor._parsers["rplog"]

        file_entry = self._GetTestOSFileEntry(["rp.log"])
        result = test_extractor._CheckParserCanProcessFileEntry(parser, file_entry)
        self.assertTrue(result)

        # Test with a file entry with a different name.
        file_entry = self._GetTestOSFileEntry(["recycler", "INFO2"])
        result = test_extractor._CheckParserCanProcessFileEntry(parser, file_entry)
        self.assertFalse(result)

    def testGetSignatureMatchParserNames(self):
        """Tests the _GetSignatureMatchParserNames function."""
        test_extractor = extractors.EventDataExtractor(
            parser_filter_expression="recycle_bin_info2,winevtx"
        )

        file_entry = self._GetTestOSFileEntry(["evtx", "System.evtx"])
        file_object = file_entry.GetFileObject()

        parser_names = test_extractor._GetSignatureMatchParserNames(file_object)
        self.assertEqual(parser_names, ["winevtx"])

        # Test with a file that does not match a signature.
        file_entry = self._GetTestOSFileEntry(["recycler", "INFO2"])
        file_object = file_entry.GetFileObject()

        parser_names = test_extractor._GetSignatureMatchParserNames(file_object)
        self.assertEqual(parser_names, [])

    def testInitializeParserObjects(self):
        """Tests the _InitializeParserObjects function."""
        test_extractor = extractors.EventDataExtractor(
            parser_filter_expression="filestat,mft,recycle_bin_info2,usnjrnl,winevtx"
        )

        # The filestat and usnjrnl parsers are kept separate from the other parsers.
        self.assertEqual(
            sorted(test_extractor._parsers.keys()),
            ["mft", "recycle_bin_info2", "winevtx"],
        )
        self.assertEqual(test_extractor._filestat_parser.NAME, "filestat")
        self.assertEqual(test_extractor._mft_parser.NAME, "mft")
        self.assertEqual(test_extractor._usnjrnl_parser.NAME, "usnjrnl")

        # Parsers with format signatures are not in the non-signature parsers.
        self.assertEqual(
            test_extractor._non_sigscan_parser_names, {"recycle_bin_info2"}
        )
        self.assertIsNotNone(test_extractor._format_scanner)

        test_extractor._InitializeParserObjects(
            parser_filter_expression="recycle_bin_info2"
        )

        self.assertEqual(list(test_extractor._parsers.keys()), ["recycle_bin_info2"])
        self.assertIsNone(test_extractor._filestat_parser)
        self.assertIsNone(test_extractor._mft_parser)
        self.assertIsNone(test_extractor._usnjrnl_parser)

    def testParseDataStreamWithParser(self):
        """Tests the _ParseDataStreamWithParser function."""
        test_extractor = extractors.EventDataExtractor(
            parser_filter_expression="recycle_bin_info2"
        )

        file_entry = self._GetTestOSFileEntry(["recycler", "INFO2"])

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=file_entry
        )

        parser = test_extractor._parsers["recycle_bin_info2"]
        test_extractor._ParseDataStreamWithParser(
            parser_mediator, parser, file_entry, ""
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4)

        # Test with a data stream that does not exist.
        with self.assertRaises(RuntimeError):
            test_extractor._ParseDataStreamWithParser(
                parser_mediator, parser, file_entry, "bogus"
            )

    def testParseFileEntryWithParser(self):
        """Tests the _ParseFileEntryWithParser function."""
        test_extractor = extractors.EventDataExtractor(
            parser_filter_expression="filestat,recycle_bin,recycle_bin_info2"
        )

        file_entry = self._GetTestOSFileEntry(["recycler", "INFO2"])

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=file_entry
        )

        # Test with a file object parser.
        parser = test_extractor._parsers["recycle_bin_info2"]
        result = test_extractor._ParseFileEntryWithParser(
            parser_mediator, parser, file_entry, file_object=file_entry.GetFileObject()
        )
        self.assertEqual(result, test_extractor._PARSE_RESULT_SUCCESS)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4)

        # Test with a file entry parser.
        result = test_extractor._ParseFileEntryWithParser(
            parser_mediator, test_extractor._filestat_parser, file_entry
        )
        self.assertEqual(result, test_extractor._PARSE_RESULT_SUCCESS)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 5)

        # Test with a parser that does not support the file.
        parser = test_extractor._parsers["recycle_bin"]
        result = test_extractor._ParseFileEntryWithParser(
            parser_mediator, parser, file_entry, file_object=file_entry.GetFileObject()
        )
        self.assertEqual(result, test_extractor._PARSE_RESULT_UNSUPPORTED)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 5)

        # Test with an object that is not a parser.
        with self.assertRaises(TypeError):
            test_extractor._ParseFileEntryWithParser(parser_mediator, None, file_entry)

    def testParseFileEntryWithParsers(self):
        """Tests the _ParseFileEntryWithParsers function."""
        test_extractor = extractors.EventDataExtractor(
            parser_filter_expression="recycle_bin,recycle_bin_info2,rplog"
        )

        file_entry = self._GetTestOSFileEntry(["recycler", "INFO2"])

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=file_entry
        )

        result = test_extractor._ParseFileEntryWithParsers(
            parser_mediator,
            ["recycle_bin_info2"],
            file_entry,
            file_object=file_entry.GetFileObject(),
        )
        self.assertEqual(result, test_extractor._PARSE_RESULT_SUCCESS)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4)

        # Test with a parser of which the filters do not match the file entry.
        result = test_extractor._ParseFileEntryWithParsers(
            parser_mediator,
            ["rplog"],
            file_entry,
            file_object=file_entry.GetFileObject(),
        )
        self.assertEqual(result, test_extractor._PARSE_RESULT_SUCCESS)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4)

        # Test without parsers.
        result = test_extractor._ParseFileEntryWithParsers(
            parser_mediator, [], file_entry, file_object=file_entry.GetFileObject()
        )
        self.assertEqual(result, test_extractor._PARSE_RESULT_UNSUPPORTED)

        # Test with a parser that does not support the file.
        result = test_extractor._ParseFileEntryWithParsers(
            parser_mediator,
            ["recycle_bin"],
            file_entry,
            file_object=file_entry.GetFileObject(),
        )
        self.assertEqual(result, test_extractor._PARSE_RESULT_UNSUPPORTED)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4)

        # Test with a parser that is not enabled.
        with self.assertRaises(RuntimeError):
            test_extractor._ParseFileEntryWithParsers(
                parser_mediator,
                ["winevtx"],
                file_entry,
                file_object=file_entry.GetFileObject(),
            )

    def testParseDataStream(self):
        """Tests the ParseDataStream function."""
        test_file_path = self._GetTestFilePath(["recycler", "INFO2"])
        self._SkipIfPathNotExists(test_file_path)

        test_extractor = extractors.EventDataExtractor(
            parser_filter_expression="recycle_bin_info2"
        )

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=file_entry
        )

        test_extractor.ParseDataStream(parser_mediator, file_entry, "")

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

    def testParseDataStreamWithForceParser(self):
        """Tests the ParseDataStream function with force parser."""
        test_file_path = self._GetTestFilePath(["UsnJrnl.raw"])
        self._SkipIfPathNotExists(test_file_path)

        test_extractor = extractors.EventDataExtractor(
            force_parser=True, parser_filter_expression="usnjrnl"
        )

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=file_entry
        )

        test_extractor.ParseDataStream(parser_mediator, file_entry, "")

        number_of_events = storage_writer.GetNumberOfAttributeContainers("event")
        self.assertEqual(number_of_events, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

    def testParseFileEntryMetadata(self):
        """Tests the ParseFileEntryMetadata function."""
        file_entry = self._GetTestOSFileEntry(["recycler", "INFO2"])

        test_extractor = extractors.EventDataExtractor(
            parser_filter_expression="filestat,recycle_bin_info2"
        )

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=file_entry
        )

        test_extractor.ParseFileEntryMetadata(parser_mediator, file_entry)

        # Only the file system metadata is parsed, not the content.
        event_data_types = [
            event_data.data_type
            for event_data in storage_writer.GetAttributeContainers("event_data")
        ]
        self.assertEqual(event_data_types, ["fs:stat"])

        # Test without the filestat parser.
        test_extractor = extractors.EventDataExtractor(
            parser_filter_expression="recycle_bin_info2"
        )

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=file_entry
        )

        test_extractor.ParseFileEntryMetadata(parser_mediator, file_entry)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

    def testParseMetadataFile(self):
        """Tests the ParseMetadataFile function."""
        test_extractor = extractors.EventDataExtractor(
            parser_filter_expression="mft,usnjrnl"
        )

        # Test a $MFT metadata file.
        file_entry = self._GetTestNTFSFileEntry("/$MFT")

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=file_entry
        )

        test_extractor.ParseMetadataFile(parser_mediator, file_entry, "")

        event_data_types = collections.Counter(
            [
                event_data.data_type
                for event_data in storage_writer.GetAttributeContainers("event_data")
            ]
        )
        expected_event_data_types = {
            "fs:stat:ntfs": 46,
            "windows:distributed_link_tracking:creation": 2,
        }
        self.assertEqual(event_data_types, expected_event_data_types)

        # Test a $UsnJrnl metadata file.
        file_entry = self._GetTestNTFSFileEntry("/$Extend/$UsnJrnl", data_stream="$J")

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=file_entry
        )

        test_extractor.ParseMetadataFile(parser_mediator, file_entry, "$J")

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 19)

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.assertEqual(event_data.data_type, "fs:ntfs:usn_change")

        # Test a $UsnJrnl metadata file with a data stream other than $J.
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=file_entry
        )

        test_extractor.ParseMetadataFile(parser_mediator, file_entry, "$Max")

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        # Test a file that is not a metadata file.
        file_entry = self._GetTestOSFileEntry(["recycler", "INFO2"])

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(
            storage_writer, file_entry=file_entry
        )

        test_extractor.ParseMetadataFile(parser_mediator, file_entry, "")

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)


class PathSpecExtractorTest(test_lib.EngineTestCase):
    """Tests for the path specification extractor."""

    # pylint: disable=protected-access

    def _GetFilePaths(self, path_specs):
        """Retrieves file paths from path specifications.

        Args:
          path_specs (list[dfvfs.PathSpec]): path specifications.

        Returns:
          list[str]: file paths.
        """
        file_paths = []
        for path_spec in path_specs:
            data_stream = getattr(path_spec, "data_stream", None)
            location = getattr(path_spec, "location", None)
            if location is not None:
                if data_stream:
                    location = f"{location:s}:{data_stream:s}"
                file_paths.append(location)

        return file_paths

    def _GetFindSpecs(self, location_expressions):
        """Retrieves find specifications from location expressions.

        Args:
          location_expressions (list[str]): location regular expressions.

        Returns:
          list[dfvfs.FindSpec]: find specifications for the file system searcher.
        """
        find_specs = []
        for location_expression in location_expressions:
            find_spec = file_system_searcher.FindSpec(
                case_sensitive=False,
                location_regex=location_expression,
                location_separator="/",
            )
            find_specs.append(find_spec)

        return find_specs

    def _GetTestNTFSPathSpec(self, location):
        """Retrieves a path specification of the NTFS file system in a test image.

        Args:
          location (str): location of the file entry in the NTFS file system.

        Returns:
          dfvfs.PathSpec: path specification.

        Raises:
          SkipTest: if the path inside the test data directory does not exist and
              the test should be skipped.
        """
        # Note that the source file is a RAW (VMDK flat) image.
        test_file_path = self._GetTestFilePath(["multi_partition_image.vmdk"])
        self._SkipIfPathNotExists(test_file_path)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
            location="/p1",
            part_index=2,
            start_offset=0x00010000,
            parent=path_spec,
        )
        return path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK, location=location, parent=path_spec
        )

    def testExtractPathSpecsFromDirectory(self):
        """Tests the _ExtractPathSpecsFromDirectory function."""
        test_file_path = self._GetTestFilePath(["testdir"])
        self._SkipIfPathNotExists(test_file_path)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

        test_extractor = extractors.PathSpecExtractor()

        path_specs = list(test_extractor._ExtractPathSpecsFromDirectory(file_entry))
        paths = self._GetFilePaths(path_specs)

        expected_paths = [
            os.path.join(test_file_path, "filter2.txt"),
            os.path.join(test_file_path, "filter_1.txt"),
            os.path.join(test_file_path, "filter_3.txt"),
        ]
        self.assertEqual(sorted(paths), expected_paths)

        # Test a directory with sub directories.
        path_spec = self._GetTestNTFSPathSpec("/$Extend")
        file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

        path_specs = list(test_extractor._ExtractPathSpecsFromDirectory(file_entry))
        paths = self._GetFilePaths(path_specs)

        expected_paths = [
            "/$Extend/$ObjId",
            "/$Extend/$Quota",
            "/$Extend/$Reparse",
            "/$Extend/$RmMetadata",
            "/$Extend/$RmMetadata/$Repair",
            "/$Extend/$RmMetadata/$Repair:$Config",
            "/$Extend/$RmMetadata/$TxfLog",
        ]
        self.assertEqual(sorted(paths), expected_paths)

        # Test with the maximum recursion depth.
        with self.assertRaises(errors.MaximumRecursionDepth):
            list(
                test_extractor._ExtractPathSpecsFromDirectory(
                    file_entry, depth=test_extractor._MAXIMUM_DEPTH
                )
            )

    def testExtractPathSpecsFromFile(self):
        """Tests the _ExtractPathSpecsFromFile function."""
        test_extractor = extractors.PathSpecExtractor()

        # Test a file with a default data stream.
        path_spec = self._GetTestNTFSPathSpec("/file1.txt")
        file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

        path_specs = list(test_extractor._ExtractPathSpecsFromFile(file_entry))
        paths = self._GetFilePaths(path_specs)
        self.assertEqual(paths, ["/file1.txt"])

        # Test a file with a default and an alternate data stream.
        path_spec = self._GetTestNTFSPathSpec("/$BadClus")
        file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

        path_specs = list(test_extractor._ExtractPathSpecsFromFile(file_entry))
        paths = self._GetFilePaths(path_specs)
        self.assertEqual(sorted(paths), ["/$BadClus", "/$BadClus:$Bad"])

        # The path specification of the file entry should not be changed.
        self.assertIsNone(getattr(file_entry.path_spec, "data_stream", None))

        # Test a directory without a data stream.
        path_spec = self._GetTestNTFSPathSpec("/$Extend")
        file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

        path_specs = list(test_extractor._ExtractPathSpecsFromFile(file_entry))
        paths = self._GetFilePaths(path_specs)
        self.assertEqual(paths, ["/$Extend"])

    def testExtractPathSpecsFromFileSystem(self):
        """Tests the _ExtractPathSpecsFromFileSystem function."""
        path_spec = self._GetTestNTFSPathSpec("/")
        resolver_context = context.Context()
        test_extractor = extractors.PathSpecExtractor()

        # Test with recursion into the file system.
        path_specs = list(
            test_extractor._ExtractPathSpecsFromFileSystem(
                path_spec, resolver_context=resolver_context
            )
        )
        paths = self._GetFilePaths(path_specs)
        self.assertEqual(len(paths), 22)
        self.assertIn("/file1.txt", paths)
        self.assertIn("/$Extend/$RmMetadata/$Repair:$Config", paths)

        # Test without recursion into the file system.
        path_specs = list(
            test_extractor._ExtractPathSpecsFromFileSystem(
                path_spec, recurse_file_system=False, resolver_context=resolver_context
            )
        )
        self.assertEqual(path_specs, [path_spec])

        # Test with find specifications.
        find_specs = self._GetFindSpecs(["/file[0-9][.]txt"])
        path_specs = list(
            test_extractor._ExtractPathSpecsFromFileSystem(
                path_spec, find_specs=find_specs, resolver_context=resolver_context
            )
        )
        paths = self._GetFilePaths(path_specs)
        self.assertEqual(sorted(paths), ["/file1.txt", "/file2.txt"])

        # Test with a path specification that does not contain a file system.
        test_file_path = self._GetTestFilePath(["recycler", "INFO2"])
        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK, location="/", parent=os_path_spec
        )
        path_specs = list(
            test_extractor._ExtractPathSpecsFromFileSystem(
                path_spec, resolver_context=resolver_context
            )
        )
        self.assertEqual(path_specs, [])

    def testExtractPathSpecsFileSystem(self):
        """Tests the ExtractPathSpecs function on the file system."""
        test_file_paths = []

        test_file_path = self._GetTestFilePath(["syslog.bz2"])
        self._SkipIfPathNotExists(test_file_path)
        test_file_paths.append(test_file_path)

        test_file_path = self._GetTestFilePath(["syslog.tgz"])
        self._SkipIfPathNotExists(test_file_path)
        test_file_paths.append(test_file_path)

        test_file_path = self._GetTestFilePath(["syslog.zip"])
        self._SkipIfPathNotExists(test_file_path)
        test_file_paths.append(test_file_path)

        test_file_path = self._GetTestFilePath(["utmp", "wtmp.1"])
        self._SkipIfPathNotExists(test_file_path)
        test_file_paths.append(test_file_path)

        with shared_test_lib.TempDirectory() as temp_directory:
            for a_file in test_file_paths:
                shutil.copy(a_file, temp_directory)

            source_path_spec = path_spec_factory.Factory.NewPathSpec(
                dfvfs_definitions.TYPE_INDICATOR_OS, location=temp_directory
            )
            resolver_context = context.Context()
            test_extractor = extractors.PathSpecExtractor()
            path_specs = list(
                test_extractor.ExtractPathSpecs(
                    source_path_spec, resolver_context=resolver_context
                )
            )
            self.assertEqual(len(path_specs), 4)

    def testExtractPathSpecsFileSystemWithFindSpecs(self):
        """Tests the ExtractPathSpecs function with find specifications."""
        test_file_path = self._GetTestFilePath(["evtx", "System.evtx"])
        self._SkipIfPathNotExists(test_file_path)

        test_file_path = self._GetTestFilePath(["testdir", "filter_1.txt"])
        self._SkipIfPathNotExists(test_file_path)

        test_file_path = self._GetTestFilePath(["testdir", "filter_3.txt"])
        self._SkipIfPathNotExists(test_file_path)

        location_expressions = [
            "/test_data/testdir/filter_.+[.]txt",
            "/test_data/.+[.]evtx",
            "/test_data/evtx/.+[.]evtx",
            "/AUTHORS",
            "/does_not_exist/some_file_[0-9]+txt",
        ]
        source_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location="."
        )
        resolver_context = context.Context()
        test_extractor = extractors.PathSpecExtractor()

        find_specs = self._GetFindSpecs(location_expressions)
        path_specs = list(
            test_extractor.ExtractPathSpecs(
                source_path_spec,
                find_specs=find_specs,
                resolver_context=resolver_context,
            )
        )
        # Two files with test_data/testdir/filter_*.txt, AUTHORS,
        # test_data/evtx/System.evtx and test_data/evtx/System2.evtx and a symbolic link
        # test_data/link_to_System.evtx.
        self.assertEqual(len(path_specs), 6)

        paths = self._GetFilePaths(path_specs)

        current_directory = os.getcwd()

        expected_path = os.path.join(
            current_directory, "test_data", "testdir", "filter_1.txt"
        )
        self.assertTrue(expected_path in paths)

        expected_path = os.path.join(
            current_directory, "test_data", "testdir", "filter_2.txt"
        )
        self.assertFalse(expected_path in paths)

        expected_path = os.path.join(
            current_directory, "test_data", "testdir", "filter_3.txt"
        )
        self.assertTrue(expected_path in paths)

        expected_path = os.path.join(current_directory, "AUTHORS")
        self.assertTrue(expected_path in paths)

    def testExtractPathSpecsStorageMediaImage(self):
        """Tests the ExtractPathSpecs function an image file.

        The image file contains the following files:
        * logs/hidden.zip
        * logs/sys.tgz

        The hidden.zip file contains one file, syslog, which is the
        same for sys.tgz.

        The end results should therefore be:
        * logs/hidden.zip (unchanged)
        * logs/hidden.zip:syslog (the text file extracted out)
        * logs/sys.tgz (unchanged)
        * logs/sys.tgz (read as a GZIP file, so not compressed)
        * logs/sys.tgz:syslog.gz (A GZIP file from the TAR container)
        * logs/sys.tgz:syslog.gz:syslog (the extracted syslog file)

        This means that the collection script should collect 6 files in total.
        """
        test_file_path = self._GetTestFilePath(["syslog_image.dd"])
        self._SkipIfPathNotExists(test_file_path)

        volume_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        source_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK, location="/", parent=volume_path_spec
        )
        resolver_context = context.Context()
        test_extractor = extractors.PathSpecExtractor()
        path_specs = list(
            test_extractor.ExtractPathSpecs(
                source_path_spec, resolver_context=resolver_context
            )
        )
        self.assertEqual(len(path_specs), 3)

    def testExtractPathSpecsStorageMediaImageWithFilter(self):
        """Tests the ExtractPathSpecs function on an image file with a filter."""
        location_expressions = [
            "/a_directory/.+zip",
            "/a_directory/another.+",
            "/passwords.txt",
        ]
        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        volume_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        source_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK, location="/", parent=volume_path_spec
        )
        resolver_context = context.Context()
        test_extractor = extractors.PathSpecExtractor()

        find_specs = self._GetFindSpecs(location_expressions)
        path_specs = list(
            test_extractor.ExtractPathSpecs(
                source_path_spec,
                find_specs=find_specs,
                resolver_context=resolver_context,
            )
        )
        self.assertEqual(len(path_specs), 2)

        paths = self._GetFilePaths(path_specs)

        # path_specs[0]
        # path_spec_type: TSK
        # file_path: '/a_directory/another_file'
        # container_path: 'test_data/ímynd.dd'
        # image_offset: 0
        self.assertEqual(paths[0], "/a_directory/another_file")

        # path_specs[1]
        # path_spec_type: TSK
        # file_path: '/passwords.txt'
        # container_path: 'test_data/ímynd.dd'
        # image_offset: 0
        self.assertEqual(paths[1], "/passwords.txt")

    def testExtractPathSpecsStorageMediaImageWithPartitions(self):
        """Tests the ExtractPathSpecs function an image file with partitions.

        The image file contains 2 partitions, p1 and p2, both with a NFTS file systems.
        """
        # Note that the source file is a RAW (VMDK flat) image.
        test_file_path = self._GetTestFilePath(["multi_partition_image.vmdk"])
        self._SkipIfPathNotExists(test_file_path)

        image_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        p1_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
            location="/p1",
            part_index=2,
            start_offset=0x00010000,
            parent=image_path_spec,
        )
        source_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK, location="/", parent=p1_path_spec
        )
        test_extractor = extractors.PathSpecExtractor()

        resolver_context = context.Context()
        path_specs = list(
            test_extractor.ExtractPathSpecs(
                source_path_spec, resolver_context=resolver_context
            )
        )
        expected_paths = [
            "/$AttrDef",
            "/$BadClus",
            "/$BadClus:$Bad",
            "/$Bitmap",
            "/$Boot",
            "/$Extend",
            "/$Extend/$ObjId",
            "/$Extend/$Quota",
            "/$Extend/$Reparse",
            "/$Extend/$RmMetadata",
            "/$Extend/$RmMetadata/$Repair",
            "/$Extend/$RmMetadata/$Repair:$Config",
            "/$Extend/$RmMetadata/$TxfLog",
            "/$LogFile",
            "/$MFT",
            "/$MFTMirr",
            "/$Secure",
            "/$Secure:$SDS",
            "/$UpCase",
            "/$Volume",
            "/file1.txt",
            "/file2.txt",
        ]
        paths = self._GetFilePaths(path_specs)

        self.assertEqual(len(path_specs), len(expected_paths))
        self.assertEqual(sorted(paths), sorted(expected_paths))

        p2_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
            location="/p2",
            part_index=3,
            start_offset=0x00510000,
            parent=image_path_spec,
        )
        source_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK, location="/", parent=p2_path_spec
        )
        path_specs = list(
            test_extractor.ExtractPathSpecs(
                source_path_spec, resolver_context=resolver_context
            )
        )
        expected_paths = [
            "/$AttrDef",
            "/$BadClus",
            "/$BadClus:$Bad",
            "/$Bitmap",
            "/$Boot",
            "/$Extend",
            "/$Extend/$ObjId",
            "/$Extend/$Quota",
            "/$Extend/$Reparse",
            "/$Extend/$RmMetadata",
            "/$Extend/$RmMetadata/$Repair",
            "/$Extend/$RmMetadata/$Repair:$Config",
            "/$Extend/$RmMetadata/$TxfLog",
            "/$LogFile",
            "/$MFT",
            "/$MFTMirr",
            "/$Secure",
            "/$Secure:$SDS",
            "/$UpCase",
            "/$Volume",
            "/file1_on_part_2.txt",
            "/file2_on_part_2.txt",
        ]
        paths = self._GetFilePaths(path_specs)

        self.assertEqual(len(path_specs), len(expected_paths))
        self.assertEqual(sorted(paths), sorted(expected_paths))


if __name__ == "__main__":
    unittest.main()
