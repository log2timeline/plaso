#!/usr/bin/env python3
"""Tests for the text plugins interface."""

import unittest

import pyparsing

from plaso.lib import errors
from plaso.parsers.text_plugins import android_logcat
from plaso.parsers.text_plugins import dpkg
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import postgresql

from tests.parsers import test_lib


class TextPluginTest(test_lib.ParserTestCase):
    """Tests for the text plugins interface."""

    # pylint: disable=protected-access

    _DPKG_LINE = "2009-02-25 11:45:23 conffile /etc/X11/Xsession keep\n"

    _POSTGRESQL_LINE = (
        "2022-04-12 00:16:05.527 UTC [7755] LOG:  listening on IPv4 address "
        '"127.0.0.1", port 5432\n'
    )

    _ANDROID_LOGCAT_LINE = (
        "01-01 01:02:03.123  1234  1234 D threadtime: test of default "
        "threadtime format\n"
    )

    def _GetScanStringMatch(self, plugin, string):
        """Retrieves the first match of scan_string() that starts on the first line.

        Args:
          plugin (TextPlugin): text plugin.
          string (str): string.

        Returns:
          tuple[list[object], dict[str, object], int, int]: match tokens as list
              and dictionary, start and end offset or None if there is no match
              that starts on the first line.
        """
        match = next(plugin._pyparsing_grammar.scan_string(string, max_matches=1), None)
        if match is None:
            return None

        tokens, start, end = match
        if start > 0 and "\n" in string[: start + 1]:
            return None

        return tokens.as_list(), tokens.as_dict(), start, end

    def _GetExtractionWarningMessages(self, storage_writer):
        """Retrieves the messages of the extraction warnings.

        Args:
          storage_writer (FakeStorageWriter): storage writer.

        Returns:
          list[str]: messages of the extraction warnings.
        """
        return [
            warning.message
            for warning in storage_writer.GetAttributeContainers("extraction_warning")
        ]

    def _GetFirstLineMatch(self, plugin, string):
        """Retrieves the match of _ScanFirstLineMatch().

        Args:
          plugin (TextPlugin): text plugin.
          string (str): string.

        Returns:
          tuple[list[object], dict[str, object], int, int]: match tokens as list
              and dictionary, start and end offset or None if there is no match
              that starts on the first line.
        """
        match = plugin._ScanFirstLineMatch(string)
        if match is None:
            return None

        tokens, start, end = match
        if start > 0 and "\n" in string[: start + 1]:
            return None

        return tokens.as_list(), tokens.as_dict(), start, end

    def _CheckEquivalentToScanString(self, plugin, string):
        """Checks that _ScanFirstLineMatch() is equivalent to scan_string().

        Args:
          plugin (TextPlugin): text plugin.
          string (str): string.

        Returns:
          tuple[list[object], dict[str, object], int, int]: match tokens as list
              and dictionary, start and end offset or None if there is no match
              that starts on the first line.
        """
        expected_match = self._GetScanStringMatch(plugin, string)
        match = self._GetFirstLineMatch(plugin, string)
        self.assertEqual(match, expected_match)
        return match

    def testGetValueFromStructure(self):
        """Tests the _GetValueFromStructure function."""
        plugin = dpkg.DpkgTextPlugin()

        _, structure, _, _ = plugin._ParseString(self._DPKG_LINE)

        value = plugin._GetValueFromStructure(structure, "message_body")
        self.assertEqual(value, "conffile /etc/X11/Xsession keep")

        value = plugin._GetValueFromStructure(structure, "bogus")
        self.assertIsNone(value)

        value = plugin._GetValueFromStructure(structure, "bogus", default_value="")
        self.assertEqual(value, "")

        # An empty pyparsing.ParseResults is returned as None.
        expression = pyparsing.Group(
            pyparsing.Optional(pyparsing.Word(pyparsing.nums))
        ).set_results_name("number")
        structure = expression.parse_string("")
        self.assertIsInstance(structure.get("number"), pyparsing.ParseResults)

        value = plugin._GetValueFromStructure(structure, "number", default_value="")
        self.assertIsNone(value)

    def testParseLines(self):
        """Tests the _ParseLines function."""
        plugin = dpkg.DpkgTextPlugin()

        # Lines that cannot be parsed produce a warning and are skipped.
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        data = "".join([self._DPKG_LINE, "bogus\n", self._DPKG_LINE])
        file_object = self._CreateFileObject("dpkg.log", data.encode("utf-8"))
        text_reader = text_parser.EncodedTextReader(file_object, encoding="utf-8")

        plugin._ParseLines(parser_mediator, text_reader)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        warning_messages = self._GetExtractionWarningMessages(storage_writer)
        self.assertEqual(warning_messages, ['unable to parse log line: 2 "bogus"'])

        # Parsing stops after too many consecutive lines that cannot be parsed.
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        maximum_failures = plugin._MAXIMUM_CONSECUTIVE_LINE_FAILURES
        data = "".join(["bogus\n"] * (maximum_failures + 1) + [self._DPKG_LINE])
        file_object = self._CreateFileObject("dpkg.log", data.encode("utf-8"))
        text_reader = text_parser.EncodedTextReader(file_object, encoding="utf-8")

        plugin._ParseLines(parser_mediator, text_reader)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        warning_messages = self._GetExtractionWarningMessages(storage_writer)
        self.assertEqual(len(warning_messages), maximum_failures + 2)
        self.assertEqual(
            warning_messages[-1],
            f"more than {maximum_failures:d} consecutive failures to parse lines.",
        )

    def testScanFirstLineMatch(self):
        """Tests the _ScanFirstLineMatch function."""
        test_cases = [
            (dpkg.DpkgTextPlugin(), self._DPKG_LINE),
            (postgresql.PostgreSQLTextPlugin(), self._POSTGRESQL_LINE),
            (android_logcat.AndroidLogcatTextPlugin(), self._ANDROID_LOGCAT_LINE),
        ]
        for plugin, line in test_cases:
            # Match at the start of the first line.
            test_string = line + line
            match = self._CheckEquivalentToScanString(plugin, test_string)
            self.assertIsNotNone(match)
            self.assertEqual(match[2], 0)

            # Match after leading whitespace or text on the first line. Note that
            # the PostgreSQL grammar requires the match to start at a line start.
            test_string = "   " + line + line
            match = self._CheckEquivalentToScanString(plugin, test_string)

            test_string = "bogus " + line
            match_after_text = self._CheckEquivalentToScanString(plugin, test_string)
            if plugin.NAME == "postgresql":
                self.assertIsNone(match)
                self.assertIsNone(match_after_text)
            else:
                self.assertIsNotNone(match)
                self.assertEqual(match[2], 3)
                self.assertIsNotNone(match_after_text)

            # Match at a line start after the first line.
            test_string = "bogus " + line + line
            match = self._CheckEquivalentToScanString(plugin, test_string)
            if plugin.NAME == "postgresql":
                self.assertIsNone(match)

            # Match that only starts on a later line.
            test_string = "bogus\n" + line
            match = self._CheckEquivalentToScanString(plugin, test_string)
            self.assertIsNone(match)

            # Match after a whitespace only first line.
            test_string = "   \n" + line
            self._CheckEquivalentToScanString(plugin, test_string)

            # Match after an empty first line.
            test_string = "\n" + line
            self._CheckEquivalentToScanString(plugin, test_string)

            # Tab on the first line.
            test_string = "\t" + line
            self._CheckEquivalentToScanString(plugin, test_string)
            self._CheckEquivalentToScanString(plugin, line.replace(" ", "\t", 1))

            # No match.
            test_string = "bogus\nbogus\n"
            match = self._CheckEquivalentToScanString(plugin, test_string)
            self.assertIsNone(match)

    def testParseString(self):
        """Tests the _ParseString function."""
        plugin = dpkg.DpkgTextPlugin()

        # Buffer with a newline.
        key, structure, start, end = plugin._ParseString(self._DPKG_LINE)
        tokens, expected_start, expected_end = next(
            plugin._pyparsing_grammar.scan_string(self._DPKG_LINE, max_matches=1)
        )
        self.assertEqual(key, list(tokens.keys())[0])
        self.assertEqual(structure.as_list(), tokens[0].as_list())
        self.assertEqual(structure.as_dict(), tokens[0].as_dict())
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)

        # Buffer without a newline.
        string = self._DPKG_LINE.rstrip("\n")
        key, structure, start, end = plugin._ParseString(string)
        tokens, expected_start, expected_end = next(
            plugin._pyparsing_grammar.scan_string(string, max_matches=1)
        )
        self.assertEqual(key, list(tokens.keys())[0])
        self.assertEqual(structure.as_list(), tokens[0].as_list())
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)

        with self.assertRaises(errors.ParseError):
            plugin._ParseString("bogus\n" + self._DPKG_LINE)

        with self.assertRaises(errors.ParseError):
            plugin._ParseString("bogus\nbogus\n")

    def testSetLineStructures(self):
        """Tests the _SetLineStructures function."""
        plugin = dpkg.DpkgTextPlugin()

        line_structures = [
            ("first", pyparsing.Literal("alpha") + pyparsing.Word(pyparsing.nums)),
            (
                "second",
                pyparsing.Group(pyparsing.Literal("beta")).set_results_name("second"),
            ),
        ]
        plugin._SetLineStructures(line_structures)

        self.assertTrue(plugin._pyparsing_grammar.keepTabs)
        self.assertTrue(plugin._pyparsing_first_line_grammar.keepTabs)

        key, structure, start, end = plugin._ParseString("alpha 42\n")
        self.assertEqual(key, "first")
        self.assertEqual(structure.as_list(), ["alpha", "42"])
        self.assertEqual(start, 0)
        self.assertEqual(end, 8)

        key, structure, start, end = plugin._ParseString("beta\n")
        self.assertEqual(key, "second")
        self.assertEqual(structure.as_list(), ["beta"])
        self.assertEqual(start, 0)
        self.assertEqual(end, 4)

        # The line structures replace the previous grammar.
        with self.assertRaises(errors.ParseError):
            plugin._ParseString(self._DPKG_LINE)

    def testProcess(self):
        """Tests the Process function."""
        plugin = dpkg.DpkgTextPlugin()

        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        data = "".join([self._DPKG_LINE, self._DPKG_LINE]).encode("utf-8")
        file_object = self._CreateFileObject("dpkg.log", data)

        # Process reads the file-like object from the start.
        file_object.seek(10)

        plugin.Process(parser_mediator, file_object=file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        warning_messages = self._GetExtractionWarningMessages(storage_writer)
        self.assertEqual(warning_messages, [])

        self.assertIsNone(plugin._parser_mediator)

        # Bytes that cannot be decoded are escaped and produce a warning.
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        data = b"2009-02-25 11:45:23 conffile /etc/X11/\xffXsession keep\n"
        file_object = self._CreateFileObject("dpkg.log", data)

        plugin.Process(parser_mediator, file_object=file_object)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.assertEqual(
            event_data.message_body, "conffile /etc/X11/\\xffXsession keep"
        )

        warning_messages = self._GetExtractionWarningMessages(storage_writer)
        self.assertEqual(warning_messages, ["error decoding 0xff at offset: 38"])

        self.assertIsNone(plugin._parser_mediator)


if __name__ == "__main__":
    unittest.main()
