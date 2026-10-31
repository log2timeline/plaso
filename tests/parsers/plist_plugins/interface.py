#!/usr/bin/env python3
"""Tests for the plist plugin interface."""

import plistlib
import unittest

from dfdatetime import cocoa_time as dfdatetime_cocoa_time
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

    # pylint: disable=protected-access

    def _CreateClassDefinition(self, class_name, classes=None):
        """Creates a class definition as stored in a $objects array.

        Args:
          class_name (str): class name.
          classes (Optional[list[str]]): class hierarchy, where None represents
              the class name followed by NSObject.

        Returns:
          dict[str, object]: class definition.
        """
        return {
            "$classname": class_name,
            "$classes": classes or [class_name, "NSObject"],
        }

    def testDecodeCompositeObject(self):
        """Tests the _DecodeCompositeObject function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        objects_array = [
            "$null",
            self._CreateClassDefinition("MyObject"),
            "referenced value",
        ]
        plist_property = {
            "$class": plistlib.UID(1),
            "inline": 5,
            "null": "$null",
            "referenced": plistlib.UID(2),
        }
        composite_object = test_decoder._DecodeCompositeObject(
            plist_property, objects_array, [3]
        )
        self.assertEqual(
            composite_object,
            {"inline": 5, "null": None, "referenced": "referenced value"},
        )

        # A reference back to a parent object is skipped.
        test_decoder = interface.NSKeyedArchiverDecoder()
        composite_object = test_decoder._DecodeCompositeObject(
            plist_property, objects_array, [2]
        )
        self.assertEqual(composite_object, {"inline": 5, "null": None})

    def testDecodeNSArray(self):
        """Tests the _DecodeNSArray function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        objects_array = [
            "$null",
            self._CreateClassDefinition("NSArray"),
            "first",
            "second",
        ]
        plist_property = {
            "$class": plistlib.UID(1),
            "NS.objects": [plistlib.UID(2), {"CF$UID": 3}],
        }
        ns_array = test_decoder._DecodeNSArray(plist_property, objects_array, [4])
        self.assertEqual(ns_array, ["first", "second"])

        # A reference back to a parent object is skipped.
        test_decoder = interface.NSKeyedArchiverDecoder()
        ns_array = test_decoder._DecodeNSArray(plist_property, objects_array, [3])
        self.assertEqual(ns_array, ["first"])

        # Missing NS.objects.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSArray({"$class": plistlib.UID(1)}, objects_array, [4])

        # NS.objects element that is not an UID.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSArray(
                {"$class": plistlib.UID(1), "NS.objects": ["first"]},
                objects_array,
                [4],
            )

    def testDecodeNSData(self):
        """Tests the _DecodeNSData function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        objects_array = ["$null", self._CreateClassDefinition("NSData")]

        plist_property = {"$class": plistlib.UID(1), "NS.data": b"\x01\x02\x03"}
        ns_data = test_decoder._DecodeNSData(plist_property, objects_array, [])
        self.assertEqual(ns_data, b"\x01\x02\x03")

        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSData({"$class": plistlib.UID(1)}, objects_array, [])

        # NS.data that is not bytes.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSData(
                {"$class": plistlib.UID(1), "NS.data": "010203"}, objects_array, []
            )

    def testDecodeNSDate(self):
        """Tests the _DecodeNSDate function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        objects_array = ["$null", self._CreateClassDefinition("NSDate")]

        plist_property = {"$class": plistlib.UID(1), "NS.time": 394934931.5}
        ns_date = test_decoder._DecodeNSDate(plist_property, objects_array, [])
        self.assertIsInstance(ns_date, dfdatetime_cocoa_time.CocoaTime)
        self.assertEqual(ns_date.timestamp, 394934931.5)
        self.assertEqual(ns_date.CopyToDateTimeString(), "2013-07-08 00:08:51.500000")

        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSDate({"$class": plistlib.UID(1)}, objects_array, [])

        # An integer NS.time is not supported.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSDate(
                {"$class": plistlib.UID(1), "NS.time": 394934931}, objects_array, []
            )

    def testDecodeNSDictionary(self):
        """Tests the _DecodeNSDictionary function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        objects_array = [
            "$null",
            self._CreateClassDefinition("NSDictionary"),
            "key1",
            "key2",
            "value1",
            "value2",
            5,
        ]
        plist_property = {
            "$class": plistlib.UID(1),
            "NS.keys": [plistlib.UID(2), plistlib.UID(3)],
            "NS.objects": [plistlib.UID(4), plistlib.UID(5)],
        }
        ns_dictionary = test_decoder._DecodeNSDictionary(
            plist_property, objects_array, [7]
        )
        self.assertEqual(ns_dictionary, {"key1": "value1", "key2": "value2"})

        # A reference back to a parent object is skipped.
        test_decoder = interface.NSKeyedArchiverDecoder()
        ns_dictionary = test_decoder._DecodeNSDictionary(
            plist_property, objects_array, [5]
        )
        self.assertEqual(ns_dictionary, {"key1": "value1"})

        # Missing NS.keys.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSDictionary(
                {"$class": plistlib.UID(1), "NS.objects": []}, objects_array, [7]
            )

        # Mismatch between the number of NS.keys and NS.objects.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSDictionary(
                {
                    "$class": plistlib.UID(1),
                    "NS.keys": [plistlib.UID(2)],
                    "NS.objects": [],
                },
                objects_array,
                [7],
            )

        # NS.keys element that is not an UID.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSDictionary(
                {
                    "$class": plistlib.UID(1),
                    "NS.keys": ["key1"],
                    "NS.objects": [plistlib.UID(4)],
                },
                objects_array,
                [7],
            )

        # NS.keys element that does not reference a string.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSDictionary(
                {
                    "$class": plistlib.UID(1),
                    "NS.keys": [plistlib.UID(6)],
                    "NS.objects": [plistlib.UID(4)],
                },
                objects_array,
                [7],
            )

        # NS.objects element that is not an UID.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSDictionary(
                {
                    "$class": plistlib.UID(1),
                    "NS.keys": [plistlib.UID(2)],
                    "NS.objects": ["value1"],
                },
                objects_array,
                [7],
            )

    def testDecodeNSHashTable(self):
        """Tests the _DecodeNSHashTable function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        objects_array = [
            "$null",
            self._CreateClassDefinition("NSHashTable"),
            {"$class": plistlib.UID(1), "element": plistlib.UID(3)},
            "element value",
        ]
        plist_property = {
            "$0": 1,
            "$1": plistlib.UID(2),
            "$class": plistlib.UID(1),
        }
        ns_hash_table = test_decoder._DecodeNSHashTable(
            plist_property, objects_array, [4]
        )
        self.assertEqual(ns_hash_table, {"element": "element value"})

        # Missing $1.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSHashTable(
                {"$class": plistlib.UID(1)}, objects_array, [4]
            )

        # $1 that is not an UID.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSHashTable(
                {"$1": 2, "$class": plistlib.UID(1)}, objects_array, [4]
            )

        # $1 that references a parent object.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSHashTable(plist_property, objects_array, [2])

    def testDecodeNSNull(self):
        """Tests the _DecodeNSNull function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        objects_array = ["$null", self._CreateClassDefinition("NSNull")]

        ns_null = test_decoder._DecodeNSNull(
            {"$class": plistlib.UID(1)}, objects_array, []
        )
        self.assertIsNone(ns_null)

        # NSNull is decoded by the NSObject callback mechanism.
        ns_null = test_decoder._DecodeNSObject(
            {"$class": plistlib.UID(1)}, objects_array, []
        )
        self.assertIsNone(ns_null)

    def testDecodeNSObject(self):
        """Tests the _DecodeNSObject function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        objects_array = [
            "$null",
            self._CreateClassDefinition(
                "NSMutableString", ["NSMutableString", "NSString", "NSObject"]
            ),
            self._CreateClassDefinition("MyObject"),
            self._CreateClassDefinition("MyObject", ["MyObject"]),
            {"$classname": "MyObject"},
            {"$classes": ["MyObject", "NSObject"]},
        ]

        # The callback is selected using the first supported class in $classes.
        ns_object = test_decoder._DecodeNSObject(
            {"$class": plistlib.UID(1), "NS.string": "mutable string"},
            objects_array,
            [],
        )
        self.assertEqual(ns_object, "mutable string")

        ns_object = test_decoder._DecodeNSObject(
            {"$class": plistlib.UID(2), "value": 5}, objects_array, []
        )
        self.assertEqual(ns_object, {"value": 5})

        # Missing $class.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSObject({"value": 5}, objects_array, [])

        # $class that is not an UID.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSObject({"$class": 2}, objects_array, [])

        # Class without a supported callback.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSObject({"$class": plistlib.UID(3)}, objects_array, [])

        # Class without $classes.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSObject({"$class": plistlib.UID(4)}, objects_array, [])

        # Class without $classname.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSObject({"$class": plistlib.UID(5)}, objects_array, [])

    def testDecodeNSString(self):
        """Tests the _DecodeNSString function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        objects_array = ["$null", self._CreateClassDefinition("NSString")]

        plist_property = {"$class": plistlib.UID(1), "NS.string": "Some string"}
        ns_string = test_decoder._DecodeNSString(plist_property, objects_array, [])
        self.assertEqual(ns_string, "Some string")

        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSString({"$class": plistlib.UID(1)}, objects_array, [])

        # NS.string that is not a string.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSString(
                {"$class": plistlib.UID(1), "NS.string": b"Some string"},
                objects_array,
                [],
            )

    def testDecodeNSURL(self):
        """Tests the _DecodeNSURL function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        objects_array = [
            "$null",
            self._CreateClassDefinition("NSURL"),
            "file:///Users/user",
            "Documents",
            "",
            5,
        ]

        # A $null NS.base results in the NS.relative value only.
        ns_url = test_decoder._DecodeNSURL(
            {
                "$class": plistlib.UID(1),
                "NS.base": plistlib.UID(0),
                "NS.relative": plistlib.UID(2),
            },
            objects_array,
            [],
        )
        self.assertEqual(ns_url, "file:///Users/user")

        ns_url = test_decoder._DecodeNSURL(
            {
                "$class": plistlib.UID(1),
                "NS.base": plistlib.UID(2),
                "NS.relative": plistlib.UID(3),
            },
            objects_array,
            [],
        )
        self.assertEqual(ns_url, "file:///Users/user/Documents")

        # An empty NS.relative value is supported.
        ns_url = test_decoder._DecodeNSURL(
            {
                "$class": plistlib.UID(1),
                "NS.base": plistlib.UID(2),
                "NS.relative": plistlib.UID(4),
            },
            objects_array,
            [],
        )
        self.assertEqual(ns_url, "file:///Users/user/")

        # Missing NS.base.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSURL(
                {"$class": plistlib.UID(1), "NS.relative": plistlib.UID(2)},
                objects_array,
                [],
            )

        # NS.base that does not reference a string.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSURL(
                {
                    "$class": plistlib.UID(1),
                    "NS.base": plistlib.UID(5),
                    "NS.relative": plistlib.UID(3),
                },
                objects_array,
                [],
            )

        # NS.relative that does not reference a string.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSURL(
                {
                    "$class": plistlib.UID(1),
                    "NS.base": plistlib.UID(2),
                    "NS.relative": plistlib.UID(5),
                },
                objects_array,
                [],
            )

    def testDecodeNSUUID(self):
        """Tests the _DecodeNSUUID function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        objects_array = ["$null", self._CreateClassDefinition("NSUUID")]

        plist_property = {
            "$class": plistlib.UID(1),
            "NS.uuidbytes": bytes.fromhex("00112233445566778899aabbccddeeff"),
        }
        ns_uuid = test_decoder._DecodeNSUUID(plist_property, objects_array, [])
        self.assertEqual(ns_uuid, "00112233-4455-6677-8899-aabbccddeeff")

        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSUUID({"$class": plistlib.UID(1)}, objects_array, [])

        # NS.uuidbytes with an unsupported size.
        with self.assertRaises(RuntimeError):
            test_decoder._DecodeNSUUID(
                {"$class": plistlib.UID(1), "NS.uuidbytes": b"\x00" * 15},
                objects_array,
                [],
            )

    def testDecodeObject(self):
        """Tests the _DecodeObject function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        objects_array = ["$null", self._CreateClassDefinition("NSString")]

        decoded_object = test_decoder._DecodeObject(
            {"$class": plistlib.UID(1), "NS.string": "Some string"}, objects_array, []
        )
        self.assertEqual(decoded_object, "Some string")

        decoded_object = test_decoder._DecodeObject("$null", objects_array, [])
        self.assertIsNone(decoded_object)

        # Values that are not encoded objects are returned as-is.
        decoded_object = test_decoder._DecodeObject("null", objects_array, [])
        self.assertEqual(decoded_object, "null")

        decoded_object = test_decoder._DecodeObject(5, objects_array, [])
        self.assertEqual(decoded_object, 5)

        decoded_object = test_decoder._DecodeObject(
            {"NS.string": "Some string"}, objects_array, []
        )
        self.assertEqual(decoded_object, {"NS.string": "Some string"})

    def testGetClassName(self):
        """Tests the _GetClassName function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        objects_array = [
            "$null",
            self._CreateClassDefinition("NSString"),
            {"$classes": ["NSString", "NSObject"]},
        ]

        class_name = test_decoder._GetClassName(
            {"$class": plistlib.UID(1)}, objects_array
        )
        self.assertEqual(class_name, "NSString")

        class_name = test_decoder._GetClassName(
            {"$class": {"CF$UID": 1}}, objects_array
        )
        self.assertEqual(class_name, "NSString")

        # Missing $class.
        with self.assertRaises(RuntimeError):
            test_decoder._GetClassName({}, objects_array)

        # $class that is not an UID.
        with self.assertRaises(RuntimeError):
            test_decoder._GetClassName({"$class": 1}, objects_array)

        # Class without $classname.
        with self.assertRaises(RuntimeError):
            test_decoder._GetClassName({"$class": plistlib.UID(2)}, objects_array)

    def testGetPlistUID(self):
        """Tests the _GetPlistUID function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        plist_uid = test_decoder._GetPlistUID(plistlib.UID(5))
        self.assertEqual(plist_uid, 5)

        plist_uid = test_decoder._GetPlistUID({"CF$UID": 5})
        self.assertEqual(plist_uid, 5)

        # A dictionary with other keys than CF$UID is not a plist UID.
        plist_uid = test_decoder._GetPlistUID({"CF$UID": 5, "other": 1})
        self.assertIsNone(plist_uid)

        plist_uid = test_decoder._GetPlistUID(5)
        self.assertIsNone(plist_uid)

        plist_uid = test_decoder._GetPlistUID("$null")
        self.assertIsNone(plist_uid)

    # pylint: enable=protected-access

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

    def testIsEncoded(self):
        """Tests the IsEncoded function."""
        test_decoder = interface.NSKeyedArchiverDecoder()

        root_item = {"$archiver": "NSKeyedArchiver", "$version": 100000}
        result = test_decoder.IsEncoded(root_item)
        self.assertTrue(result)

        result = test_decoder.IsEncoded(
            {"$archiver": "NSKeyedArchiver", "$version": 99999}
        )
        self.assertFalse(result)

        result = test_decoder.IsEncoded({"$archiver": "MyArchiver", "$version": 100000})
        self.assertFalse(result)

        result = test_decoder.IsEncoded({"$version": 100000})
        self.assertFalse(result)

        result = test_decoder.IsEncoded([root_item])
        self.assertFalse(result)

        test_file_path = self._GetTestFilePath(["plist", "NSKeyedArchiver.plist"])
        self._SkipIfPathNotExists(test_file_path)

        with open(test_file_path, "rb") as file_object:
            encoded_plist = plistlib.load(file_object)

        result = test_decoder.IsEncoded(encoded_plist)
        self.assertTrue(result)


class PlistPathFilterTest(shared_test_lib.BaseTestCase):
    """Tests for the plist path filter."""

    def testMatch(self):
        """Tests the Match function."""
        path_filter = interface.PlistPathFilter("com.apple.Bluetooth.plist")

        result = path_filter.Match("com.apple.bluetooth.plist")
        self.assertTrue(result)

        # The filename to match is expected to be in lower case.
        result = path_filter.Match("com.apple.Bluetooth.plist")
        self.assertFalse(result)

        result = path_filter.Match("com.apple.bluetooth.plist.bak")
        self.assertFalse(result)

        result = path_filter.Match("com.apple.bluetooth")
        self.assertFalse(result)


class PrefixPlistPathFilterTest(shared_test_lib.BaseTestCase):
    """Tests for the prefix plist path filter."""

    def testMatch(self):
        """Tests the Match function."""
        path_filter = interface.PrefixPlistPathFilter("BackgroundItems-v")

        result = path_filter.Match("backgrounditems-v4.btm")
        self.assertTrue(result)

        result = path_filter.Match("backgrounditems-v")
        self.assertTrue(result)

        # The filename to match is expected to be in lower case.
        result = path_filter.Match("BackgroundItems-v4.btm")
        self.assertFalse(result)

        result = path_filter.Match("backgrounditems.btm")
        self.assertFalse(result)

        result = path_filter.Match("old-backgrounditems-v4.btm")
        self.assertFalse(result)


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
