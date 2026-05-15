#!/usr/bin/env python3
"""Tests for the dpkg.log text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import dpkg

from tests.parsers.text_plugins import test_lib


class DpkgTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the dpkg log text parser plugin."""

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = dpkg.DpkgTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(
            b"2009-02-25 11:45:23 conffile /etc/X11/Xsession keep\n"
        )
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
        plugin = dpkg.DpkgTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["dpkg.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "added_time": "2009-02-25T11:45:23",
            "body": "conffile /etc/X11/Xsession keep",
            "data_type": "linux:dpkg_log:entry",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
