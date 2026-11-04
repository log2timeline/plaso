#!/usr/bin/env python3
"""Tests for the line-based JSON (JSON-L) log format parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import jsonl_parser
from plaso.parsers import jsonl_plugins  # pylint: disable=unused-import
from plaso.parsers.jsonl_plugins import interface

from tests.parsers import test_lib


class FailingFormatCheckPlugin(interface.JSONLPlugin):
    """JSON-L plugin that fails its format check for testing."""

    NAME = "failing_format_check"
    DATA_FORMAT = "Test JSON-L file"

    def CheckRequiredFormat(self, json_dict):
        """Check if the log record has the minimal structure required by the plugin.

        Args:
          json_dict (dict): JSON dictionary of the log record.

        Raises:
          RuntimeError: always.
        """
        raise RuntimeError("format check failed")

    # pylint: disable=arguments-differ,unused-argument
    def _ParseRecord(self, parser_mediator, json_dict):
        """Extracts entries for testing.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          json_dict (dict): JSON dictionary of the log record.
        """


class FailingParseRecordPlugin(interface.JSONLPlugin):
    """JSON-L plugin that fails its parse record for testing."""

    NAME = "failing_parse_record"
    DATA_FORMAT = "Test JSON-L file"

    def CheckRequiredFormat(self, json_dict):
        """Check if the log record has the minimal structure required by the plugin.

        Args:
          json_dict (dict): JSON dictionary of the log record.

        Returns:
          bool: True if this is the correct parser, False otherwise.
        """
        return True

    # pylint: disable=arguments-differ,unused-argument
    def _ParseRecord(self, parser_mediator, json_dict):
        """Extracts entries for testing.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          json_dict (dict): JSON dictionary of the log record.

        Raises:
          ParseError: always.
        """
        raise errors.ParseError("parse record failed")


class JSONLParserTest(test_lib.ParserTestCase):
    """Tests for the line-based JSON (JSON-L) log format parser."""

    # pylint: disable=protected-access

    def testEnablePlugins(self):
        """Tests the EnablePlugins function."""
        parser = jsonl_parser.JSONLParser()

        number_of_plugins = len(parser._plugin_classes)

        parser.EnablePlugins([])
        self.assertEqual(len(parser._plugins_per_name), 0)

        parser.EnablePlugins(parser.ALL_PLUGINS)
        self.assertEqual(len(parser._plugins_per_name), number_of_plugins)

        parser.EnablePlugins(["gcp_log"])
        self.assertEqual(len(parser._plugins_per_name), 1)

    def testParse(self):
        """Tests the Parse function."""
        parser = jsonl_parser.JSONLParser()
        storage_writer = self._ParseFile(["jsonl", "gcp_logging.jsonl"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 11)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

    def testParseWithCorruptedLines(self):
        """Tests the Parse function on a file with corrupted lines."""
        parser = jsonl_parser.JSONLParser()
        storage_writer = self._ParseFile(["jsonl", "corrupted_lines.jsonl"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 3)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        extraction_warnings = list(
            storage_writer.GetAttributeContainers("extraction_warning")
        )
        self.assertEqual(len(extraction_warnings), 3)

        expected_message = (
            'unable to parse log line: 2 "{"insertId": "corrupted_1", '
            '"logName": "projects/fake-project/logs/testlog", ..."'
        )
        self.assertEqual(extraction_warnings[0].message, expected_message)

        expected_message = (
            'unable to parse log line: 5 ""corrupted log line not a json object""'
        )
        self.assertEqual(extraction_warnings[1].message, expected_message)

        expected_message = (
            'unable to parse log line: 7 "\x00\x00\x00\x00\x00\x00\x00\x00"'
        )
        self.assertEqual(extraction_warnings[2].message, expected_message)

    def testParseWithConsecutiveFailures(self):
        """Tests the Parse function on a file exceeding consecutive line failures."""
        parser = jsonl_parser.JSONLParser()
        parser.EnablePlugins(["gcp_log"])
        plugin = parser._plugins_per_name["gcp_log"]
        plugin._MAXIMUM_CONSECUTIVE_LINE_FAILURES = 0

        storage_writer = self._ParseFile(["jsonl", "corrupted_lines.jsonl"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 2)

        extraction_warnings = list(
            storage_writer.GetAttributeContainers("extraction_warning")
        )
        self.assertEqual(len(extraction_warnings), 2)
        self.assertEqual(
            extraction_warnings[1].message,
            "more than 0 consecutive failures to parse lines.",
        )

    def testParseWithNonJSONLFile(self):
        """Tests the Parse function on a file that is not JSON-L."""
        parser = jsonl_parser.JSONLParser()

        with self.assertRaises(errors.WrongParser):
            self._ParseFile(["password.csv"], parser)

    def testParseWithPluginFormatCheckError(self):
        """Tests the Parse function with a plugin that fails its format check."""
        parser = jsonl_parser.JSONLParser()
        parser._plugins_per_name = {
            FailingFormatCheckPlugin.NAME: FailingFormatCheckPlugin()
        }
        storage_writer = self._ParseFile(["jsonl", "gcp_logging.jsonl"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

    def testParseWithPluginParseRecordError(self):
        """Tests the Parse function with a plugin that fails to parse a record."""
        parser = jsonl_parser.JSONLParser()
        parser._plugins_per_name = {
            FailingParseRecordPlugin.NAME: FailingParseRecordPlugin()
        }
        storage_writer = self._ParseFile(["jsonl", "gcp_logging.jsonl"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 11)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)


if __name__ == "__main__":
    unittest.main()
