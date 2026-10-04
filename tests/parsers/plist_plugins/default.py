#!/usr/bin/env python3
"""Tests for the default plist plugin."""

import datetime
import plistlib
import unittest

from plaso.parsers.plist_plugins import default

from tests.parsers.plist_plugins import test_lib


class TestDefaultPlist(test_lib.PlistPluginTestCase):
    """Tests for the default plist plugin."""

    # Note that plistlib returns naive datetime values that are in UTC.
    _TOP_LEVEL_DICT_SINGLE_KEY = {
        "DE-00-AD-00-BE-EF": {
            "Name": "DBF Industries Slideshow Laser",
            "LastUsed": datetime.datetime(2012, 11, 2, 1, 21, 38, 997672),
        }
    }

    _TOP_LEVEL_DICT_MULTIPLE_KEYS = {
        "DeviceCache": {
            "44-00-00-00-00-04": {
                "Name": "Apple Magic Trackpad 2",
                "LMPSubversion": 796,
                "LMPVersion": 3,
                "PageScanMode": 0,
                "ClassOfDevice": 9620,
                "SupportedFeatures": b"\x00\x00\x00\x00",
                "Manufacturer": 76,
                "PageScanPeriod": 0,
                "ClockOffset": 17981,
                "LastNameUpdate": datetime.datetime(2012, 11, 2, 1, 21, 38, 997672),
                "InquiryRSSI": 198,
                "PageScanRepetitionMode": 1,
                "LastServicesUpdate": datetime.datetime(2012, 11, 2, 1, 13, 23),
                "displayName": "Apple Magic Trackpad 2",
                "LastInquiryUpdate": datetime.datetime(2012, 11, 2, 1, 13, 17, 324095),
                "Services": "",
                "BatteryPercent": 0.61,
            },
            "44-00-00-00-00-02": {
                "Name": "test-macpro",
                "ClockOffset": 28180,
                "ClassOfDevice": 3670276,
                "PageScanMode": 0,
                "LastNameUpdate": datetime.datetime(2011, 4, 7, 17, 56, 53, 524275),
                "PageScanPeriod": 2,
                "PageScanRepetitionMode": 1,
                "LastInquiryUpdate": datetime.datetime(2012, 7, 10, 22, 5, 0, 20116),
            },
        }
    }

    def testProcessSingle(self):
        """Tests Process on a plist containing a root, value and timestamp."""
        plugin = default.DefaultPlugin()
        storage_writer = self._ParsePlistWithPlugin(
            plugin, "single", self._TOP_LEVEL_DICT_SINGLE_KEY
        )

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

        expected_event_values = {
            "data_type": "plist:key",
            "key": "LastUsed",
            "root": "/DE-00-AD-00-BE-EF",
            "written_time": "2012-11-02T01:21:38.997672+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)
        self.assertFalse(event_data.written_time.is_local_time)

    def testProcessMulti(self):
        """Tests Process on a plist containing five keys with date values."""
        plugin = default.DefaultPlugin()
        storage_writer = self._ParsePlistWithPlugin(
            plugin, "nested", self._TOP_LEVEL_DICT_MULTIPLE_KEYS
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 5)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "plist:key",
            "key": "LastNameUpdate",
            "root": "/DeviceCache/44-00-00-00-00-02",
            "written_time": "2011-04-07T17:56:53.524275+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithPlistlibDates(self):
        """Tests Process on dates read by plistlib from XML and binary plists."""
        xml_plist = (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b'<plist version="1.0"><dict><key>Device</key><dict>'
            b"<key>LastUsed</key><date>2012-11-02T01:21:38Z</date>"
            b"</dict></dict></plist>\n"
        )
        binary_plist = plistlib.dumps(
            {"Device": {"LastUsed": datetime.datetime(2012, 11, 2, 1, 21, 38)}},
            fmt=plistlib.FMT_BINARY,
        )

        expected_event_values = {
            "data_type": "plist:key",
            "key": "LastUsed",
            "root": "/Device",
            "written_time": "2012-11-02T01:21:38.000000+00:00",
        }

        plugin = default.DefaultPlugin()
        for plist_data in (xml_plist, binary_plist):
            top_level_object = plistlib.loads(plist_data)

            # plistlib returns the UTC date as a naive datetime value.
            datetime_value = top_level_object["Device"]["LastUsed"]
            self.assertIsNone(datetime_value.tzinfo)

            storage_writer = self._ParsePlistWithPlugin(
                plugin, "plistlib", top_level_object
            )

            number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
                "event_data"
            )
            self.assertEqual(number_of_event_data, 1)

            event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
            self.CheckEventData(event_data, expected_event_values)
            self.assertFalse(event_data.written_time.is_local_time)


if __name__ == "__main__":
    unittest.main()
