#!/usr/bin/env python3
"""Tests for the Microsoft Internet Explorer (MSIE) Cache Files (CF) parser."""

import unittest

from plaso.parsers import msiecf

from tests.parsers import test_lib


class MSIECFParserTest(test_lib.ParserTestCase):
    """Tests for the MSIE Cache Files (MSIECF) parser."""

    def testParseWithContentIE5(self):
        """Tests the Parse function on a Content.IE5 index.dat file."""
        parser = msiecf.MSIECFParser()
        storage_writer = self._ParseFile(["msiecf", "Content.IE5", "index.dat"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 35)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "access_time": "2015-08-25T11:05:37.1370000+00:00",
            "cache_directory_index": 2,
            "cached_file_size": 1150,
            "creation_time": None,
            "data_type": "msiecf:url",
            "expiration_time": "2016-02-21T11:05:36+00:00",
            "last_visited_time": None,
            "modification_time": "2013-10-19T01:08:06.0000000+00:00",
            "number_of_hits": 3,
            "offset": 25472,
            "primary_time": None,
            "secondary_time": None,
            "synchronization_time": "2015-08-25T11:05:36+00:00",
            "url": "http://www.bing.com/favicon.ico",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 2)
        self.CheckEventData(event_data, expected_event_values)

        expected_event_values = {
            "data_type": "msiecf:redirected",
            "offset": 27392,
            "url": "http://go.microsoft.com/fwlink/?LinkId=299196",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 7)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithHistoryIE5(self):
        """Tests the Parse function on a History.IE5 index.dat file."""
        parser = msiecf.MSIECFParser()
        storage_writer = self._ParseFile(["msiecf", "History.IE5", "index.dat"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 17)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "access_time": None,
            "cache_directory_index": -2,
            "cached_file_size": 0,
            "creation_time": None,
            "data_type": "msiecf:url",
            "expiration_time": "2015-09-20T10:58:10+00:00",
            "last_visited_time": "2015-08-25T11:05:18.5120000+00:00",
            "modification_time": None,
            "number_of_hits": 1,
            "offset": 20480,
            "primary_time": None,
            "secondary_time": "2015-08-25T11:05:18.5120000+00:00",
            "synchronization_time": "2015-08-25T11:05:20+00:00",
            "url": "Visited: gold_administrator@http://www.msn.com/?ocid=iehp",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithLeak(self):
        """Tests the Parse function with leak records."""
        parser = msiecf.MSIECFParser()
        storage_writer = self._ParseFile(["msiecf", "nfury_index.dat"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1035)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "cache_directory_index": 1,
            "cache_directory_name": "VUQHQA73",
            "cached_file_size": 1966,
            "cached_filename": "ADSAdClient31[1].htm",
            "data_type": "msiecf:leak",
            "offset": 26368,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 4)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
