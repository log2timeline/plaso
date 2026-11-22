#!/usr/bin/env python3
"""Tests for the output mediator object."""

import os
import unittest

import pytz

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import artifacts
from plaso.lib import definitions
from plaso.storage.fake import writer as fake_writer
from plaso.output import mediator

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class OutputMediatorTest(test_lib.OutputModuleTestCase):
    """Tests for the output mediator object."""

    # pylint: disable=protected-access

    _TEST_EVENTS = [
        {
            "data_type": "test:event",
            "filename": "log/syslog.1",
            "hostname": "ubuntu",
            "text": (
                "Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n "
                "closed for user root)"
            ),
            "timestamp": "2012-06-27 18:17:01",
            "timestamp_desc": definitions.TIME_DESCRIPTION_METADATA_MODIFICATION,
            "username": "root",
        }
    ]

    _TSK_PATH_SPEC = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK,
        inode=15,
        location="/var/log/syslog.1",
        parent=path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS,
            location=os.path.join(os.path.sep, "cases", "image.dd"),
        ),
    )

    def testReadMessageFormattersFile(self):
        """Tests the _ReadMessageFormattersFile function."""
        test_file_path = self._GetTestFilePath(["formatters", "format_test.yaml"])
        self._SkipIfPathNotExists(test_file_path)

        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            output_mediator = mediator.OutputMediator(storage_writer)

            output_mediator._ReadMessageFormattersFile(test_file_path)
            self.assertEqual(len(output_mediator._message_formatters), 2)
        finally:
            storage_writer.Close()

    def testGetDisplayNameForPathSpec(self):
        """Tests the GetDisplayNameForPathSpec function."""
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            output_mediator = mediator.OutputMediator(storage_writer)

            display_name = output_mediator.GetDisplayNameForPathSpec(
                self._TSK_PATH_SPEC
            )
            self.assertEqual(display_name, "TSK:/var/log/syslog.1")

            display_name = output_mediator.GetDisplayNameForPathSpec(None)
            self.assertIsNone(display_name)

        finally:
            storage_writer.Close()

    def testGetHostname(self):
        """Tests the GetHostname function."""
        system_configuration = artifacts.SystemConfigurationArtifact()
        system_configuration.hostname = artifacts.HostnameArtifact(name="myhost")

        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            storage_writer.AddAttributeContainer(system_configuration)

            output_mediator = mediator.OutputMediator(storage_writer)

            _, event_data, _ = containers_test_lib.CreateEventFromValues(
                self._TEST_EVENTS[0]
            )
            hostname = output_mediator.GetHostname(event_data)
            self.assertEqual(hostname, "ubuntu")

            event_data.hostname = None

            hostname = output_mediator.GetHostname(event_data)
            self.assertEqual(hostname, "-")

        finally:
            storage_writer.Close()

    def testGetHostnameWithFallback(self):
        """Tests the GetHostname function with pre-processing fallback."""
        system_configuration = artifacts.SystemConfigurationArtifact()
        system_configuration.hostname = artifacts.HostnameArtifact(name="myhost")

        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            storage_writer.AddAttributeContainer(system_configuration)

            output_mediator = mediator.OutputMediator(
                storage_writer,
                use_fallback_hostname=True,
            )
            _, event_data, _ = containers_test_lib.CreateEventFromValues(
                self._TEST_EVENTS[0]
            )
            hostname = output_mediator.GetHostname(event_data)
            self.assertEqual(hostname, "ubuntu")

            event_data.hostname = None

            hostname = output_mediator.GetHostname(event_data)
            self.assertEqual(hostname, "myhost")

        finally:
            storage_writer.Close()

    def testGetMACBRepresentation(self):
        """Tests the GetMACBRepresentation function."""
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            output_mediator = mediator.OutputMediator(storage_writer)

            event, event_data, _ = containers_test_lib.CreateEventFromValues(
                self._TEST_EVENTS[0]
            )
            macb_representation = output_mediator.GetMACBRepresentation(
                event, event_data
            )
            self.assertEqual(macb_representation, "..C.")

        finally:
            storage_writer.Close()

    def testGetMACBRepresentationFromDescriptions(self):
        """Tests the GetMACBRepresentationFromDescriptions function."""
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            output_mediator = mediator.OutputMediator(storage_writer)

            macb_representation = output_mediator.GetMACBRepresentationFromDescriptions(
                []
            )
            self.assertEqual(macb_representation, "....")

            macb_representation = output_mediator.GetMACBRepresentationFromDescriptions(
                [
                    definitions.TIME_DESCRIPTION_CREATION,
                    definitions.TIME_DESCRIPTION_MODIFICATION,
                ]
            )
            self.assertEqual(macb_representation, "M..B")

            macb_representation = output_mediator.GetMACBRepresentationFromDescriptions(
                ["mtime", "atime", "ctime", "crtime"]
            )
            self.assertEqual(macb_representation, "MACB")

            macb_representation = output_mediator.GetMACBRepresentationFromDescriptions(
                [
                    definitions.TIME_DESCRIPTION_LAST_ACCESS,
                    definitions.TIME_DESCRIPTION_METADATA_MODIFICATION,
                ]
            )
            self.assertEqual(macb_representation, ".AC.")

        finally:
            storage_writer.Close()

    def testGetMessageFormatter(self):
        """Tests the GetMessageFormatter function."""
        test_file_path = self._GetTestFilePath(["formatters", "format_test.yaml"])
        self._SkipIfPathNotExists(test_file_path)

        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            output_mediator = mediator.OutputMediator(storage_writer)

            message_formatter = output_mediator.GetMessageFormatter("test:event")
            self.assertIsNone(message_formatter)

            output_mediator.ReadMessageFormattersFromFile(test_file_path)

            message_formatter = output_mediator.GetMessageFormatter("TEST:EVENT")
            self.assertIsNotNone(message_formatter)
            self.assertEqual(message_formatter.data_type, "test:event")

            message = message_formatter.GetMessage({"text": "My text"})
            self.assertEqual(message, "My text")

            message_formatter = output_mediator.GetMessageFormatter("test:bogus")
            self.assertIsNone(message_formatter)

        finally:
            storage_writer.Close()

    def testGetRelativePathForPathSpec(self):
        """Tests the GetRelativePathForPathSpec function."""
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            output_mediator = mediator.OutputMediator(storage_writer)

            relative_path = output_mediator.GetRelativePathForPathSpec(
                self._TSK_PATH_SPEC
            )
            self.assertEqual(relative_path, "/var/log/syslog.1")

            relative_path = output_mediator.GetRelativePathForPathSpec(None)
            self.assertIsNone(relative_path)

        finally:
            storage_writer.Close()

    def testGetSourceMapping(self):
        """Tests the GetSourceMapping function."""
        test_file_path = self._GetTestFilePath(["formatters", "format_test.yaml"])
        self._SkipIfPathNotExists(test_file_path)

        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            output_mediator = mediator.OutputMediator(storage_writer)

            output_mediator.ReadMessageFormattersFromFile(test_file_path)

            source_mapping = output_mediator.GetSourceMapping("TEST:EVENT")
            self.assertEqual(source_mapping, ("FILE", "Test log file"))

            source_mapping = output_mediator.GetSourceMapping("test:bogus")
            self.assertEqual(source_mapping, (None, None))

        finally:
            storage_writer.Close()

    def testGetUsername(self):
        """Tests the GetUsername function."""
        test_user1 = artifacts.UserAccountArtifact(
            identifier="1000",
            path_separator="\\",
            user_directory="C:\\Users\\testuser1",
            username="testuser1",
        )
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            output_mediator = mediator.OutputMediator(storage_writer)

            storage_writer.AddAttributeContainer(test_user1)

            _, event_data, _ = containers_test_lib.CreateEventFromValues(
                self._TEST_EVENTS[0]
            )
            username = output_mediator.GetUsername(event_data)
            self.assertEqual(username, "root")

            event_data.username = None
            setattr(event_data, "user_sid", "1000")

            username = output_mediator.GetUsername(event_data)
            self.assertEqual(username, "testuser1")

            # Test that the cached username is returned on a subsequent lookup.
            username = output_mediator.GetUsername(event_data)
            self.assertEqual(username, "testuser1")

            setattr(event_data, "user_sid", "1001")

            username = output_mediator.GetUsername(event_data)
            self.assertEqual(username, "-")

        finally:
            storage_writer.Close()

    def testReadMessageFormattersFromDirectory(self):
        """Tests the ReadMessageFormattersFromDirectory function."""
        test_directory_path = self._GetTestFilePath(["formatters"])
        self._SkipIfPathNotExists(test_directory_path)

        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            output_mediator = mediator.OutputMediator(storage_writer)

            output_mediator.ReadMessageFormattersFromDirectory(test_directory_path)
            self.assertEqual(len(output_mediator._message_formatters), 2)

        finally:
            storage_writer.Close()

    def testReadMessageFormattersFromFile(self):
        """Tests the ReadMessageFormattersFromFile function."""
        test_file_path = self._GetTestFilePath(["formatters", "format_test.yaml"])
        self._SkipIfPathNotExists(test_file_path)

        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            output_mediator = mediator.OutputMediator(storage_writer)

            output_mediator.ReadMessageFormattersFromFile(test_file_path)
            self.assertEqual(len(output_mediator._message_formatters), 2)

            with self.assertRaises(KeyError):
                output_mediator.ReadMessageFormattersFromFile(test_file_path)

            output_mediator.ReadMessageFormattersFromFile(
                test_file_path, override_existing=True
            )
            self.assertEqual(len(output_mediator._message_formatters), 2)

        finally:
            storage_writer.Close()

    def testSetPreferredLanguageIdentifier(self):
        """Tests the SetPreferredLanguageIdentifier function."""
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            output_mediator = mediator.OutputMediator(storage_writer)

            output_mediator.SetPreferredLanguageIdentifier("is-IS")
            self.assertEqual(output_mediator._lcid, 0x040F)

            winevt_resources_helper = output_mediator.GetWinevtResourcesHelper()
            self.assertEqual(winevt_resources_helper._lcid, 0x040F)

            output_mediator.SetPreferredLanguageIdentifier(None)
            self.assertIsNone(output_mediator._lcid)

            winevt_resources_helper = output_mediator.GetWinevtResourcesHelper()
            self.assertEqual(winevt_resources_helper._lcid, 0x0409)

            with self.assertRaises(ValueError):
                output_mediator.SetPreferredLanguageIdentifier("bogus")

            with self.assertRaises(ValueError):
                output_mediator.SetPreferredLanguageIdentifier(1033)

        finally:
            storage_writer.Close()

    def testSetTimeZone(self):
        """Tests the SetTimeZone function."""
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            output_mediator = mediator.OutputMediator(storage_writer)

            self.assertEqual(output_mediator.time_zone, pytz.UTC)

            output_mediator.SetTimeZone("Europe/Brussels")
            self.assertEqual(
                output_mediator.time_zone, pytz.timezone("Europe/Brussels")
            )

            output_mediator.SetTimeZone(None)
            self.assertEqual(output_mediator.time_zone, pytz.UTC)

            with self.assertRaises(ValueError):
                output_mediator.SetTimeZone("Bogus/Zone")

        finally:
            storage_writer.Close()


if __name__ == "__main__":
    unittest.main()
