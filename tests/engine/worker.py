#!/usr/bin/env python3
"""Tests the event extraction worker."""

import collections
import os
import unittest

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context
from dfvfs.resolver import resolver as path_spec_resolver
from dfvfs.path import factory as path_spec_factory

from plaso.containers import events
from plaso.containers import sessions
from plaso.engine import configurations
from plaso.engine import profilers
from plaso.engine import worker
from plaso.lib import definitions
from plaso.parsers import mediator as parsers_mediator
from plaso.storage.fake import writer as fake_writer

from tests.analyzers import manager as analyzers_manager_test
from tests import test_lib as shared_test_lib


class EventExtractionWorkerTest(shared_test_lib.BaseTestCase):
    """Tests for the event extraction worker."""

    # pylint: disable=protected-access

    def _CreateParserMediator(self, storage_writer):
        """Creates a parser mediator.

        Args:
          storage_writer (StorageWriter): storage writer.

        Returns:
          ParserMediator: parser mediator.
        """
        resolver_context = context.Context()
        parser_mediator = parsers_mediator.ParserMediator(
            resolver_context=resolver_context
        )
        parser_mediator.SetStorageWriter(storage_writer)

        return parser_mediator

    def _GetEventDataOfEvent(self, storage_writer, event):
        """Retrieves the event data of an event.

        Args:
          storage_writer (FakeStorageWriter): storage writer.
          event (EventObject): event.

        Return:
          EventData: event data corresponding to the event.
        """
        event_data_identifier = event.GetEventDataIdentifier()
        return storage_writer.GetAttributeContainerByIdentifier(
            events.EventData.CONTAINER_TYPE, event_data_identifier
        )

    def _GetEventDataStreamOfEventData(self, storage_writer, event_data):
        """Retrieves the event data stream of event data.

        Args:
          storage_writer (FakeStorageWriter): storage writer.
          event_data (EventData): event data.

        Return:
          EventDataStream: event data stream corresponding to the event data.
        """
        event_data_stream_identifier = event_data.GetEventDataStreamIdentifier()
        return storage_writer.GetAttributeContainerByIdentifier(
            events.EventDataStream.CONTAINER_TYPE, event_data_stream_identifier
        )

    def _GetEventSourceLocations(self, storage_writer):
        """Retrieves the locations of the event sources.

        Args:
          storage_writer (FakeStorageWriter): storage writer.

        Returns:
          list[str]: sorted locations of the path specifications of the event
              sources.
        """
        return sorted(
            event_source.path_spec.location
            for event_source in storage_writer.GetAttributeContainers("event_source")
        )

    def _ProcessDirectoryTree(self, extraction_worker, path_spec):
        """Processes a directory tree with an extraction worker.

        Args:
          extraction_worker (EventExtractionWorker): extraction worker.
          path_spec (dfvfs.PathSpec): path specification of the root directory.

        Returns:
          collections.Counter: number of event data per data type.
        """
        resolver_context = context.Context()
        parser_mediator = parsers_mediator.ParserMediator(
            resolver_context=resolver_context
        )
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()
        parser_mediator.SetStorageWriter(storage_writer)

        extraction_worker.ProcessPathSpec(parser_mediator, path_spec)

        local_directory_path_spec = extraction_worker.PopLocalDirectoryPathSpec()
        while local_directory_path_spec:
            extraction_worker.ProcessPathSpec(
                parser_mediator, local_directory_path_spec
            )
            local_directory_path_spec = extraction_worker.PopLocalDirectoryPathSpec()

        event_source = storage_writer.GetFirstWrittenEventSource()
        while event_source:
            extraction_worker.ProcessPathSpec(parser_mediator, event_source.path_spec)
            event_source = storage_writer.GetNextWrittenEventSource()

        event_data_counts = collections.Counter(
            event_data.data_type
            for event_data in storage_writer.GetAttributeContainers("event_data")
        )

        storage_writer.Close()

        return event_data_counts

    def _GetTestFilePathSpec(self, path_segments):
        """Retrieves a path specification of a test file in the test data directory.

        Args:
          path_segments (list[str]): components of a path to a test file, relative
              to the test_data directory.

        Returns:
          dfvfs.PathSpec: path specification.

        Raises:
          SkipTest: if the path inside the test data directory does not exist and
              the test should be skipped.
        """
        test_file_path = self._GetTestFilePath(path_segments)
        self._SkipIfPathNotExists(test_file_path)

        return path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )

    def _GetTestNTFSFileEntry(self, parser_mediator, location):
        """Retrieves a file entry of the NTFS file system in a test image.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          location (str): location of the file entry in the NTFS file system.

        Returns:
          dfvfs.FileEntry: file entry.

        Raises:
          SkipTest: if the path inside the test data directory does not exist and
              the test should be skipped.
        """
        # Note that the image file is a RAW (VMDK flat) image.
        path_spec = self._GetTestFilePathSpec(["multi_partition_image.vmdk"])
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
            location="/p1",
            part_index=2,
            start_offset=0x00010000,
            parent=path_spec,
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK, location=location, parent=path_spec
        )

        return path_spec_resolver.Resolver.OpenFileEntry(
            path_spec, resolver_context=parser_mediator.resolver_context
        )

    def _TestProcessPathSpec(
        self,
        storage_writer,
        path_spec,
        expected_event_data_counts,
        archive_types_string=None,
        extraction_worker=None,
    ):
        """Tests processing a path specification.

        Args:
          storage_writer (StorageWriter): storage writer.
          path_spec (dfvfs.PathSpec): path specification.
          expected_event_data_counts (dict[str, int|list[int]]): expected counts
              of number of event data containers per data type.
          archive_types_string (Optional[str]): comma separated archive types for
              which embedded file entries should be processed.
          extraction_worker (Optional[EventExtractionWorker]): worker to process
              the path specification. If None, a new worker will be created.
        """
        session = sessions.Session()

        resolver_context = context.Context()
        parser_mediator = parsers_mediator.ParserMediator(
            resolver_context=resolver_context
        )

        parser_mediator.SetStorageWriter(storage_writer)

        if not extraction_worker:
            configuration = configurations.ExtractionConfiguration()
            configuration.archive_types_string = archive_types_string

            extraction_worker = worker.EventExtractionWorker()
            extraction_worker.SetExtractionConfiguration(configuration)

        storage_writer.Open()

        try:
            storage_writer.AddAttributeContainer(session)

            extraction_worker.ProcessPathSpec(parser_mediator, path_spec)
            event_source = storage_writer.GetFirstWrittenEventSource()
            while event_source:
                extraction_worker.ProcessPathSpec(
                    parser_mediator, event_source.path_spec
                )
                event_source = storage_writer.GetNextWrittenEventSource()

            storage_writer.UpdateAttributeContainer(session)

            if expected_event_data_counts:
                self.CheckEventDataCounts(storage_writer, expected_event_data_counts)

        finally:
            storage_writer.Close()

    def CheckEventDataCounts(self, storage_writer, expected_event_data_counts):
        """Asserts that the number of events per data type matches.

        Args:
          storage_writer (FakeStorageWriter): storage writer.
          expected_event_data_counts (dict[str, int|list[int]]): expected counts
              of number of event data containers per data type.
        """
        event_counters = collections.Counter()
        for event_data in storage_writer.GetAttributeContainers("event_data"):
            event_counters[event_data.data_type] += 1

        for data_type, expected_event_count in expected_event_data_counts.items():
            event_count = event_counters.pop(data_type, 0)
            if isinstance(expected_event_count, list):
                self.assertIn(event_count, expected_event_count)
            else:
                self.assertEqual(
                    event_count,
                    expected_event_count,
                    (f'data type: "{data_type:s}" does not match expected value'),
                )

        # Ensure there are no events left unaccounted for.
        self.assertEqual(event_counters, collections.Counter())

    def testAnalyzeDataStream(self):
        """Tests the _AnalyzeDataStream function."""
        session = sessions.Session()

        resolver_context = context.Context()
        parser_mediator = parsers_mediator.ParserMediator(
            resolver_context=resolver_context
        )

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        extraction_worker = worker.EventExtractionWorker()

        test_analyzer = analyzers_manager_test.TestAnalyzer()
        self.assertEqual(len(test_analyzer.GetResults()), 0)

        extraction_worker._analyzers = [test_analyzer]

        storage_writer.Open()

        storage_writer.AddAttributeContainer(session)

        file_entry = self._GetTestFileEntry(["syslog.tgz"])
        parser_mediator.SetFileEntry(file_entry)

        display_name = parser_mediator.GetDisplayName()
        event_data_stream = events.EventDataStream()

        extraction_worker._AnalyzeDataStream(
            file_entry, "", display_name, event_data_stream
        )

        storage_writer.UpdateAttributeContainer(session)

        storage_writer.Close()

        self.assertIsNotNone(event_data_stream)

        event_attribute = getattr(event_data_stream, "test_result", None)
        self.assertEqual(event_attribute, "is_vegetable")

    def testAnalyzeFileObject(self):
        """Tests the _AnalyzeFileObject function."""
        session = sessions.Session()

        resolver_context = context.Context()
        parser_mediator = parsers_mediator.ParserMediator(
            resolver_context=resolver_context
        )

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        extraction_worker = worker.EventExtractionWorker()

        test_analyzer = analyzers_manager_test.TestAnalyzer()
        self.assertEqual(len(test_analyzer.GetResults()), 0)

        extraction_worker._analyzers = [test_analyzer]

        storage_writer.Open()

        storage_writer.AddAttributeContainer(session)

        file_entry = self._GetTestFileEntry(["syslog.tgz"])
        parser_mediator.SetFileEntry(file_entry)

        file_object = file_entry.GetFileObject()
        display_name = parser_mediator.GetDisplayName()
        event_data_stream = events.EventDataStream()

        extraction_worker._AnalyzeFileObject(
            file_object, display_name, event_data_stream
        )

        storage_writer.UpdateAttributeContainer(session)

        storage_writer.Close()

        self.assertIsNotNone(event_data_stream)

        event_attribute = getattr(event_data_stream, "test_result", None)
        self.assertEqual(event_attribute, "is_vegetable")

    def testCanSkipDataStream(self):
        """Tests the _CanSkipDataStream function."""
        extraction_worker = worker.EventExtractionWorker()

        file_entry = self._GetTestFileEntry(["syslog.tgz"])

        result = extraction_worker._CanSkipDataStream(file_entry, None)
        self.assertFalse(result)

    def testCanSkipContentExtraction(self):
        """Tests the _CanSkipContentExtraction function."""
        extraction_worker = worker.EventExtractionWorker()

        file_entry = self._GetTestFileEntry(["syslog.tgz"])

        result = extraction_worker._CanSkipContentExtraction(file_entry)
        self.assertFalse(result)

    def testExtractContentFromDataStream(self):
        """Tests the _ExtractContentFromDataStream function."""
        session = sessions.Session()

        resolver_context = context.Context()
        parser_mediator = parsers_mediator.ParserMediator(
            resolver_context=resolver_context
        )

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        extraction_worker = worker.EventExtractionWorker(
            parser_filter_expression="filestat,text/syslog_traditional"
        )

        test_analyzer = analyzers_manager_test.TestAnalyzer()
        self.assertEqual(len(test_analyzer.GetResults()), 0)

        extraction_worker._analyzers = [test_analyzer]

        storage_writer.Open()

        storage_writer.AddAttributeContainer(session)

        file_entry = self._GetTestFileEntry(["syslog", "syslog"])
        parser_mediator.SetFileEntry(file_entry)

        extraction_worker._ExtractContentFromDataStream(parser_mediator, file_entry, "")

        storage_writer.UpdateAttributeContainer(session)

        # Only the content is extracted, so no file system metadata is expected.
        expected_event_data_counts = {"syslog:cron:task_run": 3, "syslog:line": 13}
        self.CheckEventDataCounts(storage_writer, expected_event_data_counts)

        self.assertEqual(
            extraction_worker.processing_status,
            definitions.STATUS_INDICATOR_RUNNING,
        )

        storage_writer.Close()

    def testExtractMetadataFromFileEntry(self):
        """Tests the _ExtractMetadataFromFileEntry function."""
        session = sessions.Session()

        resolver_context = context.Context()
        parser_mediator = parsers_mediator.ParserMediator(
            resolver_context=resolver_context
        )

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        extraction_worker = worker.EventExtractionWorker(
            parser_filter_expression="filestat,text/syslog_traditional"
        )

        test_analyzer = analyzers_manager_test.TestAnalyzer()
        self.assertEqual(len(test_analyzer.GetResults()), 0)

        extraction_worker._analyzers = [test_analyzer]

        storage_writer.Open()

        storage_writer.AddAttributeContainer(session)

        file_entry = self._GetTestFileEntry(["syslog", "syslog"])
        parser_mediator.SetFileEntry(file_entry)

        extraction_worker._ExtractMetadataFromFileEntry(parser_mediator, file_entry, "")

        storage_writer.UpdateAttributeContainer(session)

        # Only the file system metadata is extracted, so no content is expected.
        expected_event_data_counts = {"fs:stat": 1}
        self.CheckEventDataCounts(storage_writer, expected_event_data_counts)

        self.assertEqual(
            extraction_worker.processing_status,
            definitions.STATUS_INDICATOR_RUNNING,
        )

        storage_writer.Close()

    def testGetCompressedStreamTypes(self):
        """Tests the _GetCompressedStreamTypes function."""
        session = sessions.Session()

        resolver_context = context.Context()
        parser_mediator = parsers_mediator.ParserMediator(
            resolver_context=resolver_context
        )

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        extraction_worker = worker.EventExtractionWorker()

        test_analyzer = analyzers_manager_test.TestAnalyzer()
        self.assertEqual(len(test_analyzer.GetResults()), 0)

        extraction_worker._analyzers = [test_analyzer]

        storage_writer.Open()

        storage_writer.AddAttributeContainer(session)

        extraction_worker = worker.EventExtractionWorker()

        path_spec = self._GetTestFilePathSpec(["syslog.tgz"])

        type_indicators = extraction_worker._GetCompressedStreamTypes(
            parser_mediator, path_spec
        )
        self.assertEqual(type_indicators, [dfvfs_definitions.TYPE_INDICATOR_GZIP])

        storage_writer.UpdateAttributeContainer(session)

        storage_writer.Close()

    def testIsMetadataFile(self):
        """Tests the _IsMetadataFile function."""
        extraction_worker = worker.EventExtractionWorker()

        file_entry = self._GetTestFileEntry(["syslog.tgz"])

        result = extraction_worker._IsMetadataFile(file_entry)
        self.assertFalse(result)

    def testProcessArchiveType(self):
        """Tests the _ProcessArchiveType function."""
        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        extraction_worker = worker.EventExtractionWorker(
            parser_filter_expression="filestat"
        )

        path_spec = self._GetTestFilePathSpec(["syslog.tar"])

        storage_writer.Open()

        try:
            extraction_worker._ProcessArchiveType(
                parser_mediator, path_spec, dfvfs_definitions.TYPE_INDICATOR_TAR
            )

            event_sources = list(storage_writer.GetAttributeContainers("event_source"))
            self.assertEqual(len(event_sources), 1)

            event_source_path_spec = event_sources[0].path_spec
            self.assertEqual(
                event_source_path_spec.type_indicator,
                dfvfs_definitions.TYPE_INDICATOR_TAR,
            )
            self.assertEqual(event_source_path_spec.location, "/syslog")
            self.assertEqual(event_source_path_spec.parent, path_spec)

            self.assertEqual(
                extraction_worker.processing_status,
                definitions.STATUS_INDICATOR_COLLECTING,
            )

            # Test with a data stream that does not contain the archive type.
            path_spec = self._GetTestFilePathSpec(["syslog", "syslog"])

            extraction_worker._ProcessArchiveType(
                parser_mediator, path_spec, dfvfs_definitions.TYPE_INDICATOR_TAR
            )

            number_of_event_sources = storage_writer.GetNumberOfAttributeContainers(
                "event_source"
            )
            self.assertEqual(number_of_event_sources, 1)

        finally:
            storage_writer.Close()

    def testProcessCompressedStreamTypes(self):
        """Tests the _ProcessCompressedStreamTypes function."""
        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        extraction_worker = worker.EventExtractionWorker(
            parser_filter_expression="filestat"
        )

        path_spec = self._GetTestFilePathSpec(["syslog.bz2"])
        file_entry = self._GetTestFileEntry(["syslog.bz2"])
        parser_mediator.SetFileEntry(file_entry)

        storage_writer.Open()

        try:
            # Test without type indicators.
            extraction_worker._ProcessCompressedStreamTypes(
                parser_mediator, path_spec, []
            )

            number_of_event_sources = storage_writer.GetNumberOfAttributeContainers(
                "event_source"
            )
            self.assertEqual(number_of_event_sources, 0)

            self.assertEqual(
                extraction_worker.processing_status, definitions.STATUS_INDICATOR_IDLE
            )

            type_indicators = [
                dfvfs_definitions.TYPE_INDICATOR_BZIP2,
                dfvfs_definitions.TYPE_INDICATOR_GZIP,
                dfvfs_definitions.TYPE_INDICATOR_XZ,
                "bogus",
            ]
            extraction_worker._ProcessCompressedStreamTypes(
                parser_mediator, path_spec, type_indicators
            )

            self.assertEqual(
                extraction_worker.processing_status,
                definitions.STATUS_INDICATOR_COLLECTING,
            )

            event_sources = list(storage_writer.GetAttributeContainers("event_source"))
            self.assertEqual(len(event_sources), 3)

            event_source_path_spec = event_sources[0].path_spec
            self.assertEqual(
                event_source_path_spec.type_indicator,
                dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
            )
            self.assertEqual(
                event_source_path_spec.compression_method,
                dfvfs_definitions.COMPRESSION_METHOD_BZIP2,
            )
            self.assertEqual(event_source_path_spec.parent, path_spec)

            event_source_path_spec = event_sources[1].path_spec
            self.assertEqual(
                event_source_path_spec.type_indicator,
                dfvfs_definitions.TYPE_INDICATOR_GZIP,
            )
            self.assertEqual(event_source_path_spec.parent, path_spec)

            event_source_path_spec = event_sources[2].path_spec
            self.assertEqual(
                event_source_path_spec.type_indicator,
                dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
            )
            self.assertEqual(
                event_source_path_spec.compression_method,
                dfvfs_definitions.COMPRESSION_METHOD_XZ,
            )

            # The unsupported type indicator should result in a warning.
            warnings = list(storage_writer.GetAttributeContainers("extraction_warning"))
            self.assertEqual(len(warnings), 1)
            self.assertIn("bogus", warnings[0].message)

        finally:
            storage_writer.Close()

    def testProcessDirectory(self):
        """Tests the _ProcessDirectory function."""
        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        extraction_worker = worker.EventExtractionWorker(
            parser_filter_expression="filestat"
        )

        file_entry = self._GetTestFileEntry(["testdir"])
        parser_mediator.SetFileEntry(file_entry)

        storage_writer.Open()

        try:
            extraction_worker._ProcessDirectory(parser_mediator, file_entry)

            self.assertEqual(
                extraction_worker.processing_status,
                definitions.STATUS_INDICATOR_RUNNING,
            )

            file_names = sorted(
                [
                    os.path.basename(event_source.path_spec.location)
                    for event_source in storage_writer.GetAttributeContainers(
                        "event_source"
                    )
                ]
            )
            self.assertEqual(
                file_names, ["filter2.txt", "filter_1.txt", "filter_3.txt"]
            )

            # The directory itself is collected but not parsed.
            number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
                "event_data"
            )
            self.assertEqual(number_of_event_data, 0)

        finally:
            storage_writer.Close()

    def testProcessFileEntry(self):
        """Tests the _ProcessFileEntry function."""
        extraction_worker = worker.EventExtractionWorker(
            parser_filter_expression="filestat,mft,text/syslog_traditional"
        )

        # Test a regular file.
        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_entry = self._GetTestFileEntry(["syslog", "syslog"])
        parser_mediator.SetFileEntry(file_entry)

        storage_writer.Open()

        try:
            extraction_worker._ProcessFileEntry(parser_mediator, file_entry)

            expected_event_data_counts = {
                "fs:stat": 1,
                "syslog:cron:task_run": 3,
                "syslog:line": 13,
            }
            self.CheckEventDataCounts(storage_writer, expected_event_data_counts)

            number_of_event_data_streams = (
                storage_writer.GetNumberOfAttributeContainers("event_data_stream")
            )
            self.assertEqual(number_of_event_data_streams, 1)

        finally:
            storage_writer.Close()

        # Test a directory, of which only the metadata is extracted.
        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_entry = self._GetTestFileEntry(["testdir"])
        parser_mediator.SetFileEntry(file_entry)

        storage_writer.Open()

        try:
            extraction_worker._ProcessFileEntry(parser_mediator, file_entry)

            expected_event_data_counts = {"fs:stat": 1}
            self.CheckEventDataCounts(storage_writer, expected_event_data_counts)

            number_of_event_sources = storage_writer.GetNumberOfAttributeContainers(
                "event_source"
            )
            self.assertEqual(number_of_event_sources, 0)

        finally:
            storage_writer.Close()

        # Test a NTFS metadata file.
        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_entry = self._GetTestNTFSFileEntry(parser_mediator, "/$MFT")
        parser_mediator.SetFileEntry(file_entry)

        storage_writer.Open()

        try:
            extraction_worker._ProcessFileEntry(parser_mediator, file_entry)

            expected_event_data_counts = {"fs:stat": 1, "fs:stat:ntfs": 44}
            self.CheckEventDataCounts(storage_writer, expected_event_data_counts)

        finally:
            storage_writer.Close()

    def testProcessFileEntryDataStream(self):
        """Tests the _ProcessFileEntryDataStream function."""
        extraction_worker = worker.EventExtractionWorker(
            parser_filter_expression="filestat,text/syslog_traditional"
        )

        file_entry = self._GetTestFileEntry(["syslog", "syslog"])

        # Test with the default data stream.
        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)
        parser_mediator.SetFileEntry(file_entry)

        storage_writer.Open()

        try:
            extraction_worker._ProcessFileEntryDataStream(
                parser_mediator, file_entry, file_entry.GetDataStream("")
            )

            expected_event_data_counts = {
                "fs:stat": 1,
                "syslog:cron:task_run": 3,
                "syslog:line": 13,
            }
            self.CheckEventDataCounts(storage_writer, expected_event_data_counts)

            event_data_streams = list(
                storage_writer.GetAttributeContainers("event_data_stream")
            )
            self.assertEqual(len(event_data_streams), 1)
            self.assertEqual(event_data_streams[0].path_spec, file_entry.path_spec)

        finally:
            storage_writer.Close()

        # Test without a data stream, of which only the metadata is extracted.
        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)
        parser_mediator.SetFileEntry(file_entry)

        storage_writer.Open()

        try:
            extraction_worker._ProcessFileEntryDataStream(
                parser_mediator, file_entry, None
            )

            expected_event_data_counts = {"fs:stat": 1}
            self.CheckEventDataCounts(storage_writer, expected_event_data_counts)

            number_of_event_data_streams = (
                storage_writer.GetNumberOfAttributeContainers("event_data_stream")
            )
            self.assertEqual(number_of_event_data_streams, 0)

        finally:
            storage_writer.Close()

    def testProcessMetadataFile(self):
        """Tests the _ProcessMetadataFile function."""
        extraction_worker = worker.EventExtractionWorker(
            parser_filter_expression="filestat,mft"
        )

        # Test a $MFT metadata file, which is parsed by the MFT parser.
        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_entry = self._GetTestNTFSFileEntry(parser_mediator, "/$MFT")
        parser_mediator.SetFileEntry(file_entry)

        storage_writer.Open()

        try:
            extraction_worker._ProcessMetadataFile(parser_mediator, file_entry)

            expected_event_data_counts = {"fs:stat": 1, "fs:stat:ntfs": 44}
            self.CheckEventDataCounts(storage_writer, expected_event_data_counts)

            number_of_event_data_streams = (
                storage_writer.GetNumberOfAttributeContainers("event_data_stream")
            )
            self.assertEqual(number_of_event_data_streams, 1)

            self.assertEqual(
                extraction_worker.processing_status,
                definitions.STATUS_INDICATOR_EXTRACTING,
            )

        finally:
            storage_writer.Close()

        # Test a $BadClus metadata file, which has 2 data streams but is not
        # parsed further.
        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_entry = self._GetTestNTFSFileEntry(parser_mediator, "/$BadClus")
        parser_mediator.SetFileEntry(file_entry)

        storage_writer.Open()

        try:
            extraction_worker._ProcessMetadataFile(parser_mediator, file_entry)

            expected_event_data_counts = {"fs:stat": 1}
            self.CheckEventDataCounts(storage_writer, expected_event_data_counts)

            data_stream_names = sorted(
                [
                    getattr(event_data_stream.path_spec, "data_stream", None) or ""
                    for event_data_stream in storage_writer.GetAttributeContainers(
                        "event_data_stream"
                    )
                ]
            )
            self.assertEqual(data_stream_names, ["", "$Bad"])

        finally:
            storage_writer.Close()

    # TODO: add tests for _SetHashers
    # TODO: add tests for _SetYaraRules
    # TODO: add tests for GetAnalyzerNames

    def testProcessPathSpecFile(self):
        """Tests the ProcessPathSpec function on a file."""
        path_spec = self._GetTestFilePathSpec(["syslog", "syslog"])
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {
            "fs:stat": 1,
            "syslog:cron:task_run": 3,
            "syslog:line": 13,
        }

        self._TestProcessPathSpec(storage_writer, path_spec, expected_event_data_counts)

    def testProcessPathSpecCompressedFileGZIP(self):
        """Tests the ProcessPathSpec function on a gzip compressed file."""
        path_spec = self._GetTestFilePathSpec(["syslog.gz"])
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {
            "fs:stat": 2,
            "syslog:cron:task_run": 3,
            "syslog:line": 9,
        }

        self._TestProcessPathSpec(storage_writer, path_spec, expected_event_data_counts)

    def testProcessPathSpecCompressedFileBZIP2(self):
        """Tests the ProcessPathSpec function on a bzip2 compressed file."""
        path_spec = self._GetTestFilePathSpec(["syslog.bz2"])
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {
            "fs:stat": 1,
            "syslog:cron:task_run": 3,
            "syslog:line": 9,
        }

        self._TestProcessPathSpec(storage_writer, path_spec, expected_event_data_counts)

    def testProcessPathSpecCompressedFileXZ(self):
        """Tests the ProcessPathSpec function on a xz compressed file."""
        path_spec = self._GetTestFilePathSpec(["syslog.xz"])
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {
            "fs:stat": 1,
            "syslog:cron:task_run": 3,
            "syslog:line": 9,
        }

        self._TestProcessPathSpec(storage_writer, path_spec, expected_event_data_counts)

    def testProcessPathSpec(self):
        """Tests the ProcessPathSpec function on an archive file."""
        test_file_path = self._GetTestFilePath(["syslog.tar"])
        self._SkipIfPathNotExists(test_file_path)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TAR, location="/syslog", parent=path_spec
        )

        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {
            "fs:stat": 1,
            "syslog:cron:task_run": 3,
            "syslog:line": 9,
        }

        self._TestProcessPathSpec(storage_writer, path_spec, expected_event_data_counts)

        # Process an archive file without "process archive files" mode.
        path_spec = self._GetTestFilePathSpec(["syslog.tar"])
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {"fs:stat": 1}

        self._TestProcessPathSpec(storage_writer, path_spec, expected_event_data_counts)

        # Process an archive file with "process archive files" mode.
        path_spec = self._GetTestFilePathSpec(["syslog.tar"])
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {
            "fs:stat": 2,
            "syslog:cron:task_run": 3,
            "syslog:line": 9,
        }

        self._TestProcessPathSpec(
            storage_writer,
            path_spec,
            expected_event_data_counts,
            archive_types_string="tar,zip",
        )

    def testProcessPathSpecCompressedArchive(self):
        """Tests the ProcessPathSpec function on a compressed archive file."""
        test_file_path = self._GetTestFilePath(["syslog.tgz"])
        self._SkipIfPathNotExists(test_file_path)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=path_spec
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TAR, location="/syslog", parent=path_spec
        )

        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {
            "fs:stat": 1,
            "syslog:cron:task_run": 3,
            "syslog:line": 9,
        }

        self._TestProcessPathSpec(storage_writer, path_spec, expected_event_data_counts)

        # Process an archive file with "process archive files" mode.
        path_spec = self._GetTestFilePathSpec(["syslog.tgz"])
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {
            "fs:stat": 3,
            "syslog:cron:task_run": 3,
            "syslog:line": 9,
        }

        self._TestProcessPathSpec(
            storage_writer,
            path_spec,
            expected_event_data_counts,
            archive_types_string="tar,zip",
        )

    def testProcessPathSpecWithLocalDirectoryProcessing(self):
        """Tests the ProcessPathSpec function with local directory processing."""
        test_file_path = self._GetTestFilePath(["ext4.raw"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_EXT, location="/", parent=os_path_spec
        )

        resolver_context = context.Context()
        parser_mediator = parsers_mediator.ParserMediator(
            resolver_context=resolver_context
        )

        # Sub directories are produced as event sources by default.
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()
        parser_mediator.SetStorageWriter(storage_writer)

        extraction_worker = worker.EventExtractionWorker()
        extraction_worker.ProcessPathSpec(parser_mediator, path_spec)

        self.assertEqual(
            self._GetEventSourceLocations(storage_writer),
            ["/a_directory", "/a_link", "/lost+found", "/passwords.txt"],
        )
        self.assertIsNone(extraction_worker.PopLocalDirectoryPathSpec())

        storage_writer.Close()

        # Sub directories are processed locally.
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()
        parser_mediator.SetStorageWriter(storage_writer)

        extraction_worker = worker.EventExtractionWorker()
        extraction_worker.SetLocalDirectoryProcessing(True)
        extraction_worker.ProcessPathSpec(parser_mediator, path_spec)

        self.assertEqual(
            self._GetEventSourceLocations(storage_writer),
            ["/a_link", "/passwords.txt"],
        )

        local_directory_locations = []
        local_directory_path_spec = extraction_worker.PopLocalDirectoryPathSpec()
        while local_directory_path_spec:
            local_directory_locations.append(local_directory_path_spec.location)
            extraction_worker.ProcessPathSpec(
                parser_mediator, local_directory_path_spec
            )
            local_directory_path_spec = extraction_worker.PopLocalDirectoryPathSpec()

        self.assertEqual(
            sorted(local_directory_locations), ["/a_directory", "/lost+found"]
        )
        self.assertEqual(
            self._GetEventSourceLocations(storage_writer),
            [
                "/a_directory/a_file",
                "/a_directory/another_file",
                "/a_link",
                "/passwords.txt",
            ],
        )

        storage_writer.Close()

        # Excluded sub directories are produced as event sources.
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()
        parser_mediator.SetStorageWriter(storage_writer)

        find_spec = file_system_searcher.FindSpec(
            case_sensitive=False, location="/a_directory", location_separator="/"
        )
        extraction_worker = worker.EventExtractionWorker()
        extraction_worker.SetLocalDirectoryProcessing(
            True, excluded_find_specs=[find_spec]
        )
        extraction_worker.ProcessPathSpec(parser_mediator, path_spec)

        self.assertEqual(
            self._GetEventSourceLocations(storage_writer),
            ["/a_directory", "/a_link", "/passwords.txt"],
        )

        local_directory_path_spec = extraction_worker.PopLocalDirectoryPathSpec()
        self.assertEqual(local_directory_path_spec.location, "/lost+found")
        self.assertIsNone(extraction_worker.PopLocalDirectoryPathSpec())

        storage_writer.Close()

        # Sub directories that were not processed are produced as event sources.
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()
        parser_mediator.SetStorageWriter(storage_writer)

        extraction_worker = worker.EventExtractionWorker()
        extraction_worker.SetLocalDirectoryProcessing(True)
        extraction_worker.ProcessPathSpec(parser_mediator, path_spec)
        extraction_worker.ProduceLocalDirectoryEventSources(parser_mediator)

        self.assertEqual(
            self._GetEventSourceLocations(storage_writer),
            ["/a_directory", "/a_link", "/lost+found", "/passwords.txt"],
        )
        for event_source in storage_writer.GetAttributeContainers("event_source"):
            if event_source.path_spec.location in ("/a_directory", "/lost+found"):
                self.assertEqual(
                    event_source.file_entry_type,
                    dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY,
                )

        self.assertIsNone(extraction_worker.PopLocalDirectoryPathSpec())

        storage_writer.Close()

        # The same event data is extracted with and without local directory
        # processing.
        extraction_worker = worker.EventExtractionWorker()
        expected_event_data_counts = self._ProcessDirectoryTree(
            extraction_worker, path_spec
        )
        self.assertEqual(expected_event_data_counts["fs:stat"], 6)

        extraction_worker = worker.EventExtractionWorker()
        extraction_worker.SetLocalDirectoryProcessing(True)
        event_data_counts = self._ProcessDirectoryTree(extraction_worker, path_spec)

        self.assertEqual(event_data_counts, expected_event_data_counts)

    def testProcessPathSpecDMG(self):
        """Tests the ProcessPathSpec function on a DMG image."""
        test_file_path = self._GetTestFilePath(["hfsplus_zlib.dmg"])
        self._SkipIfPathNotExists(test_file_path)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_MODI, parent=path_spec
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_GPT, location="/p1", parent=path_spec
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_HFS, location="/", parent=path_spec
        )
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {"fs:stat": 7}

        self._TestProcessPathSpec(storage_writer, path_spec, expected_event_data_counts)

    def testProcessPathSpecTarWithDMG(self):
        """Tests the ProcessPathSpec function on a TAR with a DMG image."""
        test_file_path = self._GetTestFilePath(["hfsplus_zlib.dmg.tar"])
        self._SkipIfPathNotExists(test_file_path)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {"fs:stat": 2}

        self._TestProcessPathSpec(
            storage_writer,
            path_spec,
            expected_event_data_counts,
            archive_types_string="tar",
        )

        expected_event_data_counts = {"fs:stat": 9}

        self._TestProcessPathSpec(
            storage_writer,
            path_spec,
            expected_event_data_counts,
            archive_types_string="modi,tar",
        )

    def testProcessPathSpecISO(self):
        """Tests the ProcessPathSpec function on an ISO image."""
        test_file_path = self._GetTestFilePath(["iso9660.raw"])
        self._SkipIfPathNotExists(test_file_path)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_RAW, parent=path_spec
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK, location="/", parent=path_spec
        )
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {"fs:stat": 5}

        self._TestProcessPathSpec(storage_writer, path_spec, expected_event_data_counts)

    def testProcessPathSpecTarWithISO(self):
        """Tests the ProcessPathSpec function on a TAR with an ISO image."""
        test_file_path = self._GetTestFilePath(["iso9660.raw.tar"])
        self._SkipIfPathNotExists(test_file_path)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {"fs:stat": 2}

        self._TestProcessPathSpec(
            storage_writer,
            path_spec,
            expected_event_data_counts,
            archive_types_string="tar",
        )

        expected_event_data_counts = {"fs:stat": 7}

        self._TestProcessPathSpec(
            storage_writer,
            path_spec,
            expected_event_data_counts,
            archive_types_string="iso9660,tar",
        )

    def testProcessPathSpecVHD(self):
        """Tests the ProcessPathSpec function on a VHD image."""
        test_file_path = self._GetTestFilePath(["image.vhd"])
        self._SkipIfPathNotExists(test_file_path)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_VHDI, parent=path_spec
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_EXT, location="/", parent=path_spec
        )
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {"fs:stat": 5}

        self._TestProcessPathSpec(storage_writer, path_spec, expected_event_data_counts)

    def testProcessPathSpecTarWithVHD(self):
        """Tests the ProcessPathSpec function on a TAR with a VHD image."""
        test_file_path = self._GetTestFilePath(["image.vhd.tar"])
        self._SkipIfPathNotExists(test_file_path)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {"fs:stat": 2}

        self._TestProcessPathSpec(
            storage_writer,
            path_spec,
            expected_event_data_counts,
            archive_types_string="tar",
        )

        expected_event_data_counts = {"fs:stat": 7}

        self._TestProcessPathSpec(
            storage_writer,
            path_spec,
            expected_event_data_counts,
            archive_types_string="tar,vhdi",
        )

    def testProcessPathSpecVMDK(self):
        """Tests the ProcessPathSpec function on a VMDK with symbolic links."""
        test_file_path = self._GetTestFilePath(["image.vmdk"])
        self._SkipIfPathNotExists(test_file_path)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_VMDK, parent=path_spec
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_EXT, location="/", parent=path_spec
        )
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {"fs:stat": 6}

        self._TestProcessPathSpec(storage_writer, path_spec, expected_event_data_counts)

    # TODO: add tests for SetExtractionConfiguration

    def testSetAnalyzersProfiler(self):
        """Tests the SetAnalyzersProfiler function."""
        extraction_worker = worker.EventExtractionWorker(
            parser_filter_expression="filestat"
        )
        extraction_worker._analyzers = [analyzers_manager_test.TestAnalyzer()]

        file_entry = self._GetTestFileEntry(["syslog.tgz"])
        file_object = file_entry.GetFileObject()

        profiling_configuration = configurations.ProfilingConfiguration()

        with shared_test_lib.TempDirectory() as temp_directory:
            profiling_configuration.directory = temp_directory

            analyzers_profiler = profilers.AnalyzersProfiler(
                "test", profiling_configuration
            )
            analyzers_profiler.Start()

            try:
                extraction_worker.SetAnalyzersProfiler(analyzers_profiler)
                self.assertEqual(
                    extraction_worker._analyzers_profiler, analyzers_profiler
                )

                event_data_stream = events.EventDataStream()
                extraction_worker._AnalyzeFileObject(
                    file_object, "syslog.tgz", event_data_stream
                )

            finally:
                analyzers_profiler.Stop()

        self.assertEqual(
            list(analyzers_profiler._profile_measurements.keys()), ["testanalyze"]
        )

        extraction_worker.SetAnalyzersProfiler(None)
        self.assertIsNone(extraction_worker._analyzers_profiler)

    def testSetProcessingProfiler(self):
        """Tests the SetProcessingProfiler function."""
        extraction_worker = worker.EventExtractionWorker(
            parser_filter_expression="filestat"
        )
        extraction_worker._analyzers = [analyzers_manager_test.TestAnalyzer()]

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_entry = self._GetTestFileEntry(["syslog.tgz"])
        parser_mediator.SetFileEntry(file_entry)

        profiling_configuration = configurations.ProfilingConfiguration()

        with shared_test_lib.TempDirectory() as temp_directory:
            profiling_configuration.directory = temp_directory

            processing_profiler = profilers.ProcessingProfiler(
                "test", profiling_configuration
            )
            processing_profiler.Start()

            storage_writer.Open()

            try:
                extraction_worker.SetProcessingProfiler(processing_profiler)
                self.assertEqual(
                    extraction_worker._processing_profiler, processing_profiler
                )

                extraction_worker._ProcessFileEntryDataStream(
                    parser_mediator, file_entry, file_entry.GetDataStream("")
                )

            finally:
                storage_writer.Close()
                processing_profiler.Stop()

        self.assertEqual(
            sorted(processing_profiler._profile_measurements.keys()),
            ["analyzing", "extracting"],
        )

        extraction_worker.SetProcessingProfiler(None)
        self.assertIsNone(extraction_worker._processing_profiler)

    def testSignalAbort(self):
        """Tests the SignalAbort function."""
        extraction_worker = worker.EventExtractionWorker(
            parser_filter_expression="filestat"
        )
        self.assertFalse(extraction_worker._abort)

        extraction_worker.SignalAbort()
        self.assertTrue(extraction_worker._abort)

        # An aborted worker should no longer produce event sources.
        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_entry = self._GetTestFileEntry(["testdir"])
        parser_mediator.SetFileEntry(file_entry)

        storage_writer.Open()

        try:
            extraction_worker._ProcessDirectory(parser_mediator, file_entry)

            number_of_event_sources = storage_writer.GetNumberOfAttributeContainers(
                "event_source"
            )
            self.assertEqual(number_of_event_sources, 0)

        finally:
            storage_writer.Close()

    def testExtractionWorkerHashing(self):
        """Test that the worker sets up and runs hashing code correctly."""
        extraction_worker = worker.EventExtractionWorker()

        extraction_worker._SetHashers("md5")
        self.assertIn("hashing", extraction_worker.GetAnalyzerNames())

        path_spec = self._GetTestFilePathSpec(["empty_file"])
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {"fs:stat": 1}

        self._TestProcessPathSpec(
            storage_writer,
            path_spec,
            expected_event_data_counts,
            extraction_worker=extraction_worker,
        )

        storage_writer.Open()

        empty_file_md5 = "d41d8cd98f00b204e9800998ecf8427e"
        for event in storage_writer.GetSortedEvents():
            event_data = self._GetEventDataOfEvent(storage_writer, event)
            event_data_stream = self._GetEventDataStreamOfEventData(
                storage_writer, event_data
            )

            self.assertEqual(event_data_stream.md5_hash, empty_file_md5)

        storage_writer.Close()

    def testExtractionWorkerYara(self):
        """Tests that the worker applies Yara matching code correctly."""
        yara_rule_path = self._GetTestFilePath(["rules.yara"])
        self._SkipIfPathNotExists(yara_rule_path)

        with open(yara_rule_path, "r", encoding="utf-8") as file_object:
            rule_string = file_object.read()

        extraction_worker = worker.EventExtractionWorker()
        extraction_worker._SetYaraRules(rule_string)
        self.assertIn("yara", extraction_worker.GetAnalyzerNames())

        path_spec = self._GetTestFilePathSpec(["test_pe.exe"])
        storage_writer = fake_writer.FakeStorageWriter()

        expected_event_data_counts = {
            "fs:stat": 1,
            "pe_coff:dll_import": 2,
            "pe_coff:file": 1,
        }

        self._TestProcessPathSpec(
            storage_writer,
            path_spec,
            expected_event_data_counts,
            extraction_worker=extraction_worker,
        )

        storage_writer.Open()

        expected_yara_match = "PEfileBasic,PEfile"
        for event in storage_writer.GetSortedEvents():
            event_data = self._GetEventDataOfEvent(storage_writer, event)
            event_data_stream = self._GetEventDataStreamOfEventData(
                storage_writer, event_data
            )

            self.assertEqual(event_data_stream.yara_match, expected_yara_match)

        storage_writer.Close()


if __name__ == "__main__":
    unittest.main()
