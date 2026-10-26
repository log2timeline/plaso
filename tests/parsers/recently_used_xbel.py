#!/usr/bin/env python3
"""Tests for the GTK recently used (recently-used.xbel) parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import recently_used_xbel

from tests.parsers import test_lib


class RecentlyUsedXBELParserTest(test_lib.ParserTestCase):
    """Tests for the GTK recently used (recently-used.xbel) parser."""

    _XML_HEADER = b'<?xml version="1.0" encoding="UTF-8"?>\n'

    _XBEL_ROOT_START = (
        b'<xbel version="1.0"\n'
        b'      xmlns:bookmark="http://www.freedesktop.org/standards/'
        b'desktop-bookmarks"\n'
        b'      xmlns:mime="http://www.freedesktop.org/standards/'
        b'shared-mime-info"\n'
        b">\n"
    )

    def _ParseData(self, data):
        """Parses data with the parser.

        Args:
          data (bytes): data.

        Returns:
          FakeStorageWriter: storage writer.

        Raises:
          WrongParser: when the data cannot be parsed.
        """
        parser = recently_used_xbel.RecentlyUsedXBELParser()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        file_object = self._CreateFileObject("recently-used.xbel", data)
        parser.ParseFileObject(parser_mediator, file_object)

        return storage_writer

    def testParse(self):
        """Tests the Parse function."""
        parser = recently_used_xbel.RecentlyUsedXBELParser()
        storage_writer = self._ParseFile(["recently-used.xbel"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Bookmark with date and time values with a fraction of a second.
        expected_event_values = {
            "added_time": "2022-08-19T10:01:02.123456+00:00",
            "applications": ["Text Editor"],
            "data_type": "linux:recently_used:entry",
            "last_visited_time": "2022-08-19T10:01:02.123457+00:00",
            "mime_type": "application/vnd.oasis.opendocument.text",
            "modification_time": "2022-08-19T10:15:30.654321+00:00",
            "uri": "file:///home/user/Documents/travel%20plan.odt",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Bookmark with date and time values without a fraction of a second.
        expected_event_values = {
            "added_time": "2021-03-04T05:06:07.000000+00:00",
            "applications": ["Image Viewer", "Image Editor"],
            "data_type": "linux:recently_used:entry",
            "last_visited_time": "2021-03-04T05:06:07.000000+00:00",
            "mime_type": "image/png",
            "modification_time": "2021-03-04T05:16:07.000000+00:00",
            "uri": "file:///home/user/Pictures/garden.png",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithInvalidDateTimeValue(self):
        """Tests the Parse function with an invalid date and time value."""
        storage_writer = self._ParseData(
            self._XML_HEADER
            + self._XBEL_ROOT_START
            + b'  <bookmark href="file:///home/user/notes.txt" added="bogus"/>\n'
            b"</xbel>\n"
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        expected_event_values = {
            "added_time": None,
            "applications": None,
            "data_type": "linux:recently_used:entry",
            "uri": "file:///home/user/notes.txt",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithNonMatchingFormats(self):
        """Tests the Parse function with formats that should not match."""
        # Check a XBEL bookmarks file without the desktop bookmarks namespace.
        with self.assertRaises(errors.WrongParser):
            self._ParseData(
                self._XML_HEADER + b'<xbel version="1.0">\n'
                b'  <bookmark href="https://www.example.com/">\n'
                b"    <title>Example</title>\n"
                b"  </bookmark>\n"
                b"</xbel>\n"
            )

        # Check a XML file with a different root element.
        with self.assertRaises(errors.WrongParser):
            self._ParseData(
                self._XML_HEADER + b"<!-- <xbel -->\n"
                b'<bookmarks xmlns:bookmark="http://www.freedesktop.org/standards/'
                b'desktop-bookmarks">\n'
                b"</bookmarks>\n"
            )

        # Check a truncated recently used file.
        with self.assertRaises(errors.WrongParser):
            self._ParseData(
                self._XML_HEADER
                + self._XBEL_ROOT_START
                + b'  <bookmark href="file:///home/user/notes.txt"'
            )

        # Check a recently used file without a XML declaration.
        with self.assertRaises(errors.WrongParser):
            self._ParseData(self._XBEL_ROOT_START + b"</xbel>\n")


if __name__ == "__main__":
    unittest.main()
