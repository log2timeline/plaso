#!/usr/bin/env python3
"""Tests for the Container Runtime Interface (CRI) log text plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import cri

from tests.parsers.text_plugins import test_lib


class CRILogTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the CRI log text parser plugin."""

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = cri.CRITextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(
            b"2016-10-06T00:17:09.669794202Z stdout P log content 1\n"
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
        """Tests for the CheckRequiredFormat function."""
        plugin = cri.CRITextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["cri.log"], plugin)

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
            "data_type": "cri:container:log:entry",
            "event_datetime": "2016-10-06T00:17:09.669794202+00:00",
            "body": " log content 1",
            "stream": "stdout",
            "tag": "P",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
