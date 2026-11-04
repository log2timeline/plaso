#!/usr/bin/env python3
"""Tests for the parsers mediator."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import event_sources
from plaso.containers import events
from plaso.parsers import mediator
from plaso.storage.fake import writer as fake_writer

from tests.parsers import test_lib


class ParsersMediatorTest(test_lib.ParserTestCase):
    """Tests for the parsers mediator."""

    # pylint: disable=protected-access

    def testAppendToParserChain(self):
        """Tests the AppendToParserChain function."""
        parser_mediator = mediator.ParserMediator()

        parser_mediator.AppendToParserChain("parser")
        self.assertEqual(parser_mediator.GetParserChain(), "parser")

        parser_mediator.AppendToParserChain("plugin")
        self.assertEqual(parser_mediator.GetParserChain(), "parser/plugin")

    def testClearParserChain(self):
        """Tests the ClearParserChain function."""
        parser_mediator = mediator.ParserMediator()

        parser_mediator.AppendToParserChain("parser")
        parser_mediator.AppendToParserChain("plugin")
        self.assertEqual(parser_mediator.GetParserChain(), "parser/plugin")

        parser_mediator.ClearParserChain()
        self.assertEqual(parser_mediator.GetParserChain(), "")

        parser_mediator.AppendToParserChain("other")
        self.assertEqual(parser_mediator.GetParserChain(), "other")

    def testGetCodePage(self):
        """Tests the GetCodePage function."""
        parser_mediator = mediator.ParserMediator()

        code_page = parser_mediator.GetCodePage()
        self.assertEqual(code_page, "cp1252")

        parser_mediator.SetPreferredCodepage("UTF-8")
        code_page = parser_mediator.GetCodePage()
        self.assertEqual(code_page, "utf-8")

        parser_mediator.SetPreferredCodepage(None)
        code_page = parser_mediator.GetCodePage()
        self.assertEqual(code_page, "cp1252")

    def testGetDisplayName(self):
        """Tests the GetDisplayName function."""
        parser_mediator = mediator.ParserMediator()

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        with self.assertRaises(ValueError):
            parser_mediator.GetDisplayName(file_entry=None)

        test_file_path = self._GetTestFilePath(["syslog.gz"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)

        display_name = parser_mediator.GetDisplayName(file_entry=file_entry)

        self.assertEqual(display_name, f"OS:{test_file_path:s}")

        gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec
        )
        file_entry = path_spec_resolver.Resolver.OpenFileEntry(gzip_path_spec)

        display_name = parser_mediator.GetDisplayName(file_entry=file_entry)

        self.assertEqual(display_name, f"GZIP:{test_file_path:s}")

        test_file_path = self._GetTestFilePath(["vsstest.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec
        )
        vshadow_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_VSHADOW,
            location="/vss2",
            store_index=1,
            parent=qcow_path_spec,
        )
        tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=35,
            location="/syslog.gz",
            parent=vshadow_path_spec,
        )

        file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)

        display_name = parser_mediator.GetDisplayName(file_entry=file_entry)

        self.assertEqual(display_name, "VSS2:TSK:/syslog.gz")

        # TODO: add test with relative path.

    def testGetDisplayNameForPathSpec(self):
        """Tests the GetDisplayNameForPathSpec function."""
        parser_mediator = mediator.ParserMediator()

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        test_file_path = self._GetTestFilePath(["syslog.gz"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )

        display_name = parser_mediator.GetDisplayNameForPathSpec(os_path_spec)
        self.assertEqual(display_name, f"OS:{test_file_path:s}")

    def testGetFileEntry(self):
        """Tests the GetFileEntry function."""
        parser_mediator = mediator.ParserMediator()

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        file_entry = parser_mediator.GetFileEntry()
        self.assertIsNone(file_entry)

    def testGetFilename(self):
        """Tests the GetFilename function."""
        parser_mediator = mediator.ParserMediator()

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        filename = parser_mediator.GetFilename()
        self.assertIsNone(filename)

    def testGetLanguageTag(self):
        """Tests the GetLanguageTag function."""
        parser_mediator = mediator.ParserMediator()

        language_tag = parser_mediator.GetLanguageTag()
        self.assertEqual(language_tag, "en-us")

        parser_mediator.SetPreferredLanguage("is-IS")
        language_tag = parser_mediator.GetLanguageTag()
        self.assertEqual(language_tag, "is-is")

        parser_mediator.SetPreferredLanguage(None)
        language_tag = parser_mediator.GetLanguageTag()
        self.assertEqual(language_tag, "en-us")

        with self.assertRaises(ValueError):
            parser_mediator.SetPreferredLanguage("bogus")

    def testGetParserChain(self):
        """Tests the GetParserChain function."""
        parser_mediator = mediator.ParserMediator()

        parser_chain = parser_mediator.GetParserChain()
        self.assertEqual(parser_chain, "")

        parser_mediator.AppendToParserChain("parser")
        parser_mediator.AppendToParserChain("plugin")

        parser_chain = parser_mediator.GetParserChain()
        self.assertEqual(parser_chain, "parser/plugin")

        # Test that the cached parser chain is returned on subsequent calls.
        parser_chain = parser_mediator.GetParserChain()
        self.assertEqual(parser_chain, "parser/plugin")

    def testGetRelativePathForPathSpec(self):
        """Tests the GetRelativePathForPathSpec function."""
        parser_mediator = mediator.ParserMediator()

        test_file_path = self._GetTestFilePath(["syslog.gz"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )

        relative_path = parser_mediator.GetRelativePathForPathSpec(os_path_spec)
        self.assertEqual(relative_path, test_file_path)

        gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec
        )

        relative_path = parser_mediator.GetRelativePathForPathSpec(gzip_path_spec)
        self.assertEqual(relative_path, test_file_path)

        relative_path = parser_mediator.GetRelativePathForPathSpec(None)
        self.assertIsNone(relative_path)

    def testPopFromParserChain(self):
        """Tests the PopFromParserChain function."""
        parser_mediator = mediator.ParserMediator()

        parser_mediator.AppendToParserChain("parser")
        parser_mediator.AppendToParserChain("plugin")
        self.assertEqual(parser_mediator.GetParserChain(), "parser/plugin")

        parser_mediator.PopFromParserChain()
        self.assertEqual(parser_mediator.GetParserChain(), "parser")

        parser_mediator.PopFromParserChain()
        self.assertEqual(parser_mediator.GetParserChain(), "")

        with self.assertRaises(IndexError):
            parser_mediator.PopFromParserChain()

    def testProduceEventData(self):
        """Tests the ProduceEventData method."""
        parser_mediator = mediator.ParserMediator()

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        storage_writer.Open()

        event_data_stream = events.EventDataStream()
        parser_mediator.ProduceEventDataStream(event_data_stream)

        event_data = events.EventData()
        event_data._parser_chain = "test_parser"
        event_data.data_type = "test"

        parser_mediator.ProduceEventData(event_data)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

    # TODO: add tests for ProduceEventDataStream.

    def testProduceEventSource(self):
        """Tests the ProduceEventSource method."""
        parser_mediator = mediator.ParserMediator()

        test_file_path = self._GetTestFilePath(["syslog.gz"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        event_source = event_sources.EventSource(path_spec=os_path_spec)

        with self.assertRaises(RuntimeError):
            parser_mediator.ProduceEventSource(event_source)

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        storage_writer.Open()

        try:
            parser_mediator.ProduceEventSource(event_source)

            number_of_event_sources = storage_writer.GetNumberOfAttributeContainers(
                "event_source"
            )
            self.assertEqual(number_of_event_sources, 1)
            self.assertEqual(parser_mediator.number_of_produced_event_sources, 1)

            stored_event_source = storage_writer.GetAttributeContainerByIndex(
                "event_source", 0
            )
            self.assertEqual(stored_event_source.path_spec, os_path_spec)

        finally:
            storage_writer.Close()

    def testProduceWarning(self):
        """Tests the ProduceWarning method."""
        parser_mediator = mediator.ParserMediator()

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        storage_writer.Open()

        try:
            parser_mediator.ProduceWarning("test")

            number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
                "extraction_warning"
            )
            self.assertEqual(number_of_warnings, 1)

            number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
                "recovery_warning"
            )
            self.assertEqual(number_of_warnings, 0)

        finally:
            storage_writer.Close()

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        storage_writer.Open()

        try:
            parser_mediator.ProduceWarning("test", recovered=True)

            number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
                "extraction_warning"
            )
            self.assertEqual(number_of_warnings, 0)

            number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
                "recovery_warning"
            )
            self.assertEqual(number_of_warnings, 1)

        finally:
            storage_writer.Close()

    def testResetFileEntry(self):
        """Tests the ResetFileEntry function."""
        parser_mediator = mediator.ParserMediator()

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        parser_mediator.ResetFileEntry()

    def testSetFileEntry(self):
        """Tests the SetFileEntry function."""
        parser_mediator = mediator.ParserMediator()

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        parser_mediator.SetFileEntry(None)

    def testSetStorageWriter(self):
        """Tests the SetStorageWriter function."""
        parser_mediator = mediator.ParserMediator()

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        parser_mediator.SetStorageWriter(None)

    def testSignalAbort(self):
        """Tests the SignalAbort function."""
        parser_mediator = mediator.ParserMediator()

        storage_writer = fake_writer.FakeStorageWriter()
        parser_mediator.SetStorageWriter(storage_writer)

        parser_mediator.SignalAbort()


if __name__ == "__main__":
    unittest.main()
