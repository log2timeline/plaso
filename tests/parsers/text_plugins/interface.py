#!/usr/bin/env python3
"""Tests for the text plugins interface."""

import io
import unittest

import pyparsing

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


class TextPluginTest(test_lib.ParserTestCase):
    """Tests for the text plugins interface."""

    # pylint: disable=protected-access

    def _ProcessLines(self, lines):
        """Processes lines with the test text plugin.

        Args:
          lines (list[str]): lines of text.

        Returns:
          tuple[TestTextPlugin, list[str]]: test text plugin and messages of
              the extraction warnings.
        """
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)

        data = "".join([f"{line:s}\n" for line in lines]).encode("utf-8")
        file_object = io.BytesIO(data)

        plugin = TestTextPlugin()
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

    # TODO: add tests for _ParseLineStructure
    # TODO: add tests for _SetLineStructures
    # TODO: add tests for Process


if __name__ == "__main__":
    unittest.main()
