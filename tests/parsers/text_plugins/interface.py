#!/usr/bin/env python3
"""Tests for the text plugins interface."""

import io
import unittest

import pyparsing

from plaso.lib import errors
from plaso.parsers.text_plugins import interface

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


if __name__ == "__main__":
    unittest.main()
