#!/usr/bin/env python3
"""Tests for the text plugins interface."""

import io
import unittest

import pyparsing

from plaso.lib import errors
from plaso.parsers.text_plugins import android_logcat
from plaso.parsers.text_plugins import dpkg
from plaso.parsers.text_plugins import interface
from plaso.parsers.text_plugins import postgresql

from tests.parsers import test_lib


class TestTextPlugin(interface.TextPlugin):
    """Text plugin for testing."""

    NAME = "test"
    DATA_FORMAT = "Test text log file"

    ENCODING = "utf-8"

    _LINE_STRUCTURES = [
        (
            "record",
            pyparsing.Keyword("record")
            + pyparsing.Word(pyparsing.nums).set_results_name("number")
            + pyparsing.Suppress(pyparsing.LineEnd()),
        )
    ]

    def __init__(self):
        """Initializes a text plugin for testing."""
        super().__init__()
        self.numbers = []

    def _ParseRecord(self, parser_mediator, key, structure):
        """Parses a pyparsing structure.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          key (str): name of the parsed structure.
          structure (pyparsing.ParseResults): tokens from a parsed log line.
        """
        self.numbers.append(self._GetValueFromStructure(structure, "number"))

    def CheckRequiredFormat(self, parser_mediator, text_reader):
        """Check if the log record has the minimal structure required by the plugin.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          text_reader (EncodedTextReader): text reader.

        Returns:
          bool: True if this is the correct plugin, False otherwise.
        """
        return True


class TestTextPluginWithUnparsableRecord(TestTextPlugin):
    """Text plugin for testing that cannot parse "record 0" lines.

    A "record 0" line starts with a match of the grammar, hence a resync stops
    at it, but parsing it fails.
    """

    def _ParseString(self, string):
        """Parses a string for known grammar.

        Args:
          string (str): string.

        Returns:
          tuple[str, pyparsing.ParseResults, int, int]: key, parsed tokens, start
              and end offset.

        Raises:
          ParseError: when the string cannot be parsed by the grammar.
        """
        if string.startswith("record 0"):
            raise errors.ParseError("Unsupported record.")

        return super()._ParseString(string)


class TextPluginTest(test_lib.ParserTestCase):
    """Tests for the text plugins interface."""

    # pylint: disable=protected-access

    def _ProcessLines(self, lines, plugin_class=TestTextPlugin):
        """Processes lines with the test text plugin.

        Args:
          lines (list[str]): lines of text.
          plugin_class (Optional[type]): text plugin class.

        Returns:
          tuple[TestTextPlugin, list[str]]: test text plugin and messages of
              the extraction warnings.
        """
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        data = "".join([f"{line:s}\n" for line in lines]).encode("utf-8")
        file_object = io.BytesIO(data)

        plugin = plugin_class()
        plugin.Process(parser_mediator, file_object=file_object)

        warning_messages = [
            warning.message
            for warning in storage_writer.GetAttributeContainers("extraction_warning")
        ]
        return plugin, warning_messages

    # TODO: add tests for _GetMatchingLineStructure
    # TODO: add tests for _GetValueFromStructure

    def testParseLines(self):
        """Tests the _ParseLines function."""
        lines = ["record 1", "record 2"]
        lines.extend(["unsupported"] * 25)
        lines.extend(["record 3", "record 4"])

        plugin, warning_messages = self._ProcessLines(lines)

        self.assertEqual(plugin.numbers, ["1", "2", "3", "4"])

        # The first 21 lines that cannot be parsed produce a warning per line,
        # followed by a warning with the line range that could not be parsed.
        self.assertEqual(len(warning_messages), 22)
        self.assertEqual(
            warning_messages[0], 'unable to parse log line: 3 "unsupported"'
        )
        self.assertEqual(
            warning_messages[21],
            (
                "more than 20 consecutive failures to parse lines, unable to "
                "parse lines: 3 to 27."
            ),
        )

        # Test lines that cannot be parsed up to the end of the file.
        lines = ["record 1"]
        lines.extend(["unsupported"] * 25)

        plugin, warning_messages = self._ProcessLines(lines)

        self.assertEqual(plugin.numbers, ["1"])
        self.assertEqual(len(warning_messages), 22)
        self.assertEqual(
            warning_messages[21],
            (
                "more than 20 consecutive failures to parse lines, unable to "
                "parse lines: 2 to 26."
            ),
        )

        # Test that parsing is aborted if no line was parsed before.
        lines = ["unsupported"] * 25
        lines.extend(["record 1", "record 2"])

        plugin, warning_messages = self._ProcessLines(lines)

        self.assertEqual(plugin.numbers, [])
        self.assertEqual(len(warning_messages), 22)
        self.assertEqual(
            warning_messages[21], "more than 20 consecutive failures to parse lines."
        )

    def testParseLinesWithMultipleResyncs(self):
        """Tests the _ParseLines function with multiple resyncs."""
        lines = ["record 1"]
        lines.extend(["unsupported"] * 25)
        lines.append("record 2")
        lines.extend(["unsupported"] * 25)
        lines.append("record 3")

        plugin, warning_messages = self._ProcessLines(lines)

        self.assertEqual(plugin.numbers, ["1", "2", "3"])
        self.assertEqual(len(warning_messages), 44)
        self.assertEqual(
            warning_messages[21],
            (
                "more than 20 consecutive failures to parse lines, unable to "
                "parse lines: 2 to 26."
            ),
        )
        self.assertEqual(
            warning_messages[43],
            (
                "more than 20 consecutive failures to parse lines, unable to "
                "parse lines: 28 to 52."
            ),
        )

    def testParseLinesWithMaximumNumberOfResyncs(self):
        """Tests the _ParseLines function exceeding the maximum number of resyncs."""
        lines = ["record 1"]
        for number in range(2, 6):
            lines.extend(["unsupported"] * 25)
            lines.append(f"record {number:d}")

        plugin, warning_messages = self._ProcessLines(lines)

        # Parsing is aborted at the fourth failure run, hence "record 5" is not
        # parsed.
        self.assertEqual(plugin.numbers, ["1", "2", "3", "4"])
        self.assertEqual(len(warning_messages), 88)
        self.assertEqual(
            warning_messages[65],
            (
                "more than 20 consecutive failures to parse lines, unable to "
                "parse lines: 54 to 78."
            ),
        )
        self.assertEqual(
            warning_messages[87],
            (
                "more than 20 consecutive failures to parse lines, maximum "
                "number of resyncs: 3 reached."
            ),
        )

    def testParseLinesWithFailuresAfterResync(self):
        """Tests the _ParseLines function with failures directly after a resync."""
        lines = ["record 1"]
        lines.extend(["unsupported"] * 25)
        lines.append("record 0")
        lines.extend(["unsupported"] * 25)
        lines.append("record 2")

        plugin, warning_messages = self._ProcessLines(
            lines, plugin_class=TestTextPluginWithUnparsableRecord
        )

        # The resync stops at "record 0", which cannot be parsed, hence parsing
        # is aborted at the next failure run, since no line was parsed after
        # the resync.
        self.assertEqual(plugin.numbers, ["1"])
        self.assertEqual(len(warning_messages), 44)
        self.assertEqual(
            warning_messages[21],
            (
                "more than 20 consecutive failures to parse lines, unable to "
                "parse lines: 2 to 26."
            ),
        )
        self.assertEqual(
            warning_messages[22], 'unable to parse log line: 27 "record 0"'
        )
        self.assertEqual(
            warning_messages[43],
            (
                "more than 20 consecutive failures to parse lines, no lines "
                "parsed since the previous resync."
            ),
        )

    # TODO: add tests for _ParseLineStructure
    # TODO: add tests for _SetLineStructures
    # TODO: add tests for Process

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


if __name__ == "__main__":
    unittest.main()
