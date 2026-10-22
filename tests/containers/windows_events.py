#!/usr/bin/env python3
"""Tests for the Windows event data attribute containers."""

import unittest
import uuid

from plaso.containers import windows_events

from tests import test_lib as shared_test_lib


class WindowsDistributedLinkTrackingEventDataTest(shared_test_lib.BaseTestCase):
    """Tests for the Windows distributed link event data attribute container."""

    def testGetAttributeNames(self):
        """Tests the GetAttributeNames function."""
        attribute_container = windows_events.WindowsDistributedLinkTrackingEventData()

        expected_attribute_names = [
            "_corrupted",
            "_event_data_stream_identifier",
            "_event_values_hash",
            "_parser_chain",
            "_recovered",
            "creation_time",
            "data_type",
            "mac_address",
            "origin",
            "uuid",
        ]

        attribute_names = sorted(attribute_container.GetAttributeNames())

        self.assertEqual(attribute_names, expected_attribute_names)

    def testCreateFromUUID(self):
        """Tests the CreateFromUUID function."""
        event_data_class = windows_events.WindowsDistributedLinkTrackingEventData

        # Distributed link tracking identifier of the NeroInfoTool.lnk test file.
        # It is a version 1 UUID: its timestamp field contains the creation date
        # and time, and its node field (the last 12 hexadecimal digits) contains
        # the MAC address of the system that created it.
        uuid_object = uuid.UUID("958705b5-0d19-11df-9fe4-705ab616a5f3")
        event_data = event_data_class.CreateFromUUID(uuid_object, "NeroInfoTool.lnk")

        self.assertEqual(
            event_data.data_type, "windows:distributed_link_tracking:creation"
        )
        self.assertEqual(
            event_data.creation_time.CopyToDateTimeStringISO8601(),
            "2010-01-29T21:02:17.8401717+00:00",
        )
        self.assertEqual(event_data.mac_address, "70:5a:b6:16:a5:f3")
        self.assertEqual(event_data.origin, "NeroInfoTool.lnk")
        self.assertEqual(event_data.uuid, "958705b5-0d19-11df-9fe4-705ab616a5f3")

        # A version 4 UUID is randomly generated and contains neither a creation
        # date and time nor a MAC address, so it is not supported.
        uuid_object = uuid.UUID("f81d4fae-7dec-41d0-a765-00a0c91e6bf6")
        with self.assertRaises(ValueError):
            event_data_class.CreateFromUUID(uuid_object, "NeroInfoTool.lnk")


class WindowsShellItemFileEntryEventDataTest(shared_test_lib.BaseTestCase):
    """Tests for the Windows shell item event attribute container."""

    def testGetAttributeNames(self):
        """Tests the GetAttributeNames function."""
        attribute_container = windows_events.WindowsShellItemFileEntryEventData()

        expected_attribute_names = [
            "_corrupted",
            "_event_data_stream_identifier",
            "_event_values_hash",
            "_parser_chain",
            "_recovered",
            "access_time",
            "creation_time",
            "data_type",
            "file_reference",
            "localized_name",
            "long_name",
            "modification_time",
            "name",
            "origin",
            "shell_item_path",
        ]

        attribute_names = sorted(attribute_container.GetAttributeNames())

        self.assertEqual(attribute_names, expected_attribute_names)


class WindowsVolumeEventDataTest(shared_test_lib.BaseTestCase):
    """Tests for the Windows volume event data attribute container."""

    def testGetAttributeNames(self):
        """Tests the GetAttributeNames function."""
        attribute_container = windows_events.WindowsVolumeEventData()

        expected_attribute_names = [
            "_corrupted",
            "_event_data_stream_identifier",
            "_event_values_hash",
            "_parser_chain",
            "_recovered",
            "creation_time",
            "data_type",
            "device_path",
            "origin",
            "serial_number",
        ]

        attribute_names = sorted(attribute_container.GetAttributeNames())

        self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == "__main__":
    unittest.main()
