#!/usr/bin/env python3
"""Tests for the xchatscrollback log parser."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import xchatscrollback

from tests.parsers.text_plugins import test_lib


class XChatScrollbackLogTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the xchatscrollback log parser."""

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = xchatscrollback.XChatScrollbackLogTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(b"T 1232315916 Python interface unloaded\n")
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

        # Check non-matching format.
        file_object = io.BytesIO(
            b"Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new "
            b"content in image.dd.\n"
        )
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    def testProcess(self):
        """Tests the Process function."""
        plugin = xchatscrollback.XChatScrollbackLogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["xchatscrollback.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 10)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "added_time": "2009-01-16T02:56:19+00:00",
            "data_type": "xchat:scrollback:line",
            "text": "* Speaking now on ##plaso##",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
