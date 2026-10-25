#!/usr/bin/env python3
"""Tests for the plist plugin interface."""

import plistlib
import unittest

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import plist_event
from plaso.parsers.plist_plugins import interface

from tests import test_lib as shared_test_lib
from tests.parsers.plist_plugins import test_lib


class MockPlugin(interface.PlistPlugin):
    """Mock plugin."""

    NAME = "mock_plist_plugin"
    DATA_FORMAT = "Test plist file"

    PLIST_PATH = "mock_plist"
    PLIST_KEYS = frozenset(["DeviceCache", "PairedDevices"])

    # pylint: disable=arguments-differ
    def _ParsePlist(self, parser_mediator, **unused_kwargs):
        """Extracts entries for testing.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
        """
        event_data = plist_event.PlistTimeEventData()
        event_data.key = "LastInquiryUpdate"
        event_data.root = "/DeviceCache/44-00-00-00-00-00"
        event_data.written_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=1351827808261762
        )
        parser_mediator.ProduceEventData(event_data)


class NSKeyedArchiverDecoderTest(shared_test_lib.BaseTestCase):
    """Tests for the decoder for NSKeyedArchiver encoded plists."""

    # TODO: add tests for _DecodeCompositeObject.
    # TODO: add tests for _DecodeNSArray.
    # TODO: add tests for _DecodeNSData.
    # TODO: add tests for _DecodeNSDate.
    # TODO: add tests for _DecodeNSDictionary.
    # TODO: add tests for _DecodeNSHashTable.
    # TODO: add tests for _DecodeNSNull.
    # TODO: add tests for _DecodeNSObject.
    # TODO: add tests for _DecodeNSString.
    # TODO: add tests for _DecodeNSURL.
    # TODO: add tests for _DecodeNSUUID.
    # TODO: add tests for _DecodeObject.
    # TODO: add tests for _GetClassName.
    # TODO: add tests for _GetPlistUID.

    def testDecode(self):
        """Tests the Decode function."""
        test_file_path = self._GetTestFilePath(["plist", "NSKeyedArchiver.plist"])
        self._SkipIfPathNotExists(test_file_path)

        test_decoder = interface.NSKeyedArchiverDecoder()

        with open(test_file_path, "rb") as file_object:
            encoded_plist = plistlib.load(file_object)

        decoded_plist = test_decoder.Decode(encoded_plist)
        self.assertIsNotNone(decoded_plist)
        self.assertIn("MyString", decoded_plist)
        self.assertEqual(decoded_plist["MyString"], "Some string")

    def testDecodeWithSharedReferences(self):
        """Tests the Decode function with many references to a shared object.

        An encoded plist can reference the same object many times. This test
        builds a structure in which every level references the same child
        object twice, and verifies that each reference resolves to the same
        decoded value and that decoding terminates.
        """
        number_of_levels = 24

        class_definition = {
            "$classname": "NSArray",
            "$classes": ["NSArray", "NSObject"],
        }
        objects_array = ["$null", class_definition, "leaf"]
        leaf_uid = 2

        child_uid = leaf_uid
        for _ in range(number_of_levels):
            level_uid = len(objects_array)
            objects_array.append(
                {
                    "$class": plistlib.UID(1),
                    "NS.objects": [plistlib.UID(child_uid), plistlib.UID(child_uid)],
                }
            )
            child_uid = level_uid

        root_item = {
            "$archiver": "NSKeyedArchiver",
            "$version": 100000,
            "$objects": objects_array,
            "$top": {"root": plistlib.UID(child_uid)},
        }

        test_decoder = interface.NSKeyedArchiverDecoder()

        decoded_plist = test_decoder.Decode(root_item)

        node = decoded_plist
        depth = 0
        while isinstance(node, list):
            self.assertEqual(len(node), 2)
            # Both references to the shared child resolve to the same decoded
            # object, that is the shared object is decoded once and reused
            # rather than re-decoded for every reference.
            self.assertIs(node[0], node[1])
            node = node[0]
            depth += 1

        self.assertEqual(depth, number_of_levels)
        self.assertEqual(node, "leaf")

    def testDecodeWithObjectCycle(self):
        """Tests the Decode function with mutually referencing objects.

        Reuse of decoded objects must not change the result for objects that
        reference each other, since the decoded value of such a subtree depends
        on the path taken to reach it.
        """
        class_definition = {
            "$classname": "NSDictionary",
            "$classes": ["NSDictionary", "NSObject"],
        }
        objects_array = [
            "$null",
            class_definition,
            "a",
            "b",
            {
                "$class": plistlib.UID(1),
                "NS.keys": [plistlib.UID(3)],
                "NS.objects": [plistlib.UID(5)],
            },
            {
                "$class": plistlib.UID(1),
                "NS.keys": [plistlib.UID(2)],
                "NS.objects": [plistlib.UID(4)],
            },
            {
                "$class": plistlib.UID(1),
                "NS.keys": [plistlib.UID(2), plistlib.UID(3)],
                "NS.objects": [plistlib.UID(4), plistlib.UID(5)],
            },
        ]
        root_item = {
            "$archiver": "NSKeyedArchiver",
            "$version": 100000,
            "$objects": objects_array,
            "$top": {"root": plistlib.UID(6)},
        }

        test_decoder = interface.NSKeyedArchiverDecoder()

        decoded_plist = test_decoder.Decode(root_item)
        self.assertEqual(decoded_plist, {"a": {"b": {}}, "b": {"a": {}}})

    # TODO: add tests for IsEncoded.


# TODO: add tests for PlistPathFilter
# TODO: add tests for PrefixPlistPathFilter


class TestPlistPlugin(test_lib.PlistPluginTestCase):
    """Tests for the plist plugin interface."""

    # pylint: disable=protected-access

    def setUp(self):
        """Makes preparations before running an individual test."""
        self._top_level_dict = {
            "DeviceCache": {
                "44-00-00-00-00-04": {
                    "Name": "Apple Magic Trackpad 2",
                    "LMPSubversion": 796,
                    "Services": "",
                    "BatteryPercent": 0.61,
                },
                "44-00-00-00-00-02": {
                    "Name": "test-macpro",
                    "ClockOffset": 28180,
                    "PageScanPeriod": 2,
                    "PageScanRepetitionMode": 1,
                },
            }
        }

    def testCheckRequiredFormat(self):
        """Tests the CheckRequiredFormat function."""
        plugin = MockPlugin()

        top_level = {"DeviceCache": {}, "PairedDevices": []}
        result = plugin.CheckRequiredFormat(top_level)
        self.assertTrue(result)

        result = plugin.CheckRequiredFormat(self._top_level_dict)
        self.assertFalse(result)

        result = plugin.CheckRequiredFormat([top_level])
        self.assertFalse(result)

    def testGetKeys(self):
        """Tests the _GetKeys function."""
        # Ensure the plugin only processes if both filename and keys exist.
        plugin = MockPlugin()

        # Match DeviceCache from the root level.
        key = ["DeviceCache"]
        result = plugin._GetKeys(self._top_level_dict, key)
        self.assertEqual(len(result), 1)

        # Look for a key nested a layer beneath DeviceCache from root level.
        # Note: overriding the default depth to look deeper.
        key = ["44-00-00-00-00-02"]
        result = plugin._GetKeys(self._top_level_dict, key, depth=2)
        self.assertEqual(len(result), 1)

        # Check the value of the result was extracted as expected.
        self.assertEqual(result[key[0]]["Name"], "test-macpro")

    def testProcess(self):
        """Tests the Process function."""
        # Ensure the plugin only processes if both filename and keys exist.
        plugin = MockPlugin()

        # Test correct filename and keys.
        top_level = {"DeviceCache": 1, "PairedDevices": 1}
        storage_writer = self._ParsePlistWithPlugin(plugin, "mock_plist", top_level)

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

        # Correct filename with odd filename cAsinG. Adding an extra useless key.
        top_level = {"DeviceCache": 1, "PairedDevices": 1, "R@ndomExtraKey": 1}
        storage_writer = self._ParsePlistWithPlugin(plugin, "pLiSt_BinAry", top_level)

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

    def testRecurseKey(self):
        """Tests the _RecurseKey function."""
        plugin = MockPlugin()

        # Ensure with a depth of 1 we only return the root key.
        result = list(plugin._RecurseKey(self._top_level_dict, depth=1))
        self.assertEqual(len(result), 1)

        # Trying again with depth limit of 2 this time.
        result = list(plugin._RecurseKey(self._top_level_dict, depth=2))
        self.assertEqual(len(result), 3)

        # A depth of two should gives us root plus the two devices. Let's check.
        my_keys = []
        for unused_root, key, unused_value in result:
            my_keys.append(key)
        expected = {"DeviceCache", "44-00-00-00-00-04", "44-00-00-00-00-02"}
        self.assertTrue(expected == set(my_keys))


if __name__ == "__main__":
    unittest.main()
