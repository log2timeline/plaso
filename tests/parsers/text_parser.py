#!/usr/bin/env python3
"""This file contains the tests for the generic text parser."""

import unittest

import pyparsing

from dfvfs.file_io import fake_file_io
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context as dfvfs_context

from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface as text_plugins_interface

from tests.parsers import test_lib


class TestTextPlugin(text_plugins_interface.TextPlugin):
    """Text plugin that records the text it was asked to check."""

    NAME = "test_text_plugin"
    DATA_FORMAT = "Test text log file"

    ENCODING = "utf-8"

    _LINE_STRUCTURES = [("line", pyparsing.rest_of_line())]

    checked_lines = []

    def _ParseRecord(self, parser_mediator, key, structure):
        """Parses a pyparsing structure.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          key (str): name of the parsed structure.
          structure (pyparsing.ParseResults): tokens from a parsed log line.
        """
        return

    def CheckRequiredFormat(self, parser_mediator, text_reader):
        """Check if the log record has the minimal structure required by the plugin.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          text_reader (EncodedTextReader): text reader.

        Returns:
          bool: True if this is the correct plugin, False otherwise.
        """
        self.checked_lines.append((self.NAME, text_reader.lines))
        return False


class OtherTestTextPlugin(TestTextPlugin):
    """Other text plugin that records the text it was asked to check."""

    NAME = "other_test_text_plugin"


class EncodedTextReaderTest(test_lib.ParserTestCase):
    """Tests for encoded text reader."""

    _TEST_LINES = "\n".join(["Multiple lines", "of text", "in a single", "file."])

    _TEST_DATA = _TEST_LINES.encode("utf-8")

    def _EncodingErrorHandler(self, exception):
        """Encoding error handler.

        Args:
          exception [UnicodeDecodeError]: exception.

        Returns:
          tuple[str, int]: replacement string and number of bytes to skip.

        Raises:
          TypeError: if exception is not of type UnicodeDecodeError.
        """
        if not isinstance(exception, UnicodeDecodeError):
            raise TypeError("Unsupported exception type.")

        # pylint: disable=attribute-defined-outside-init,no-member
        byte_value = exception.object[exception.start]

        self._encoding_errors.append((exception.start, byte_value))
        return (f"\\x{byte_value:2x}", exception.start + 1)

    def testReadLine(self):
        """Tests the ReadLine function."""
        resolver_context = dfvfs_context.Context()

        test_path_spec = fake_path_spec.FakePathSpec(location="/file.txt")
        file_object = fake_file_io.FakeFile(
            resolver_context, test_path_spec, self._TEST_DATA
        )
        file_object.Open()

        text_reader = text_parser.EncodedTextReader(file_object)

        line = text_reader.ReadLine()
        self.assertEqual(line, "Multiple lines")

        line = text_reader.ReadLine()
        self.assertEqual(line, "of text")

    def testReadLines(self):
        """Tests the ReadLines function."""
        resolver_context = dfvfs_context.Context()

        test_path_spec = fake_path_spec.FakePathSpec(location="/file.txt")
        file_object = fake_file_io.FakeFile(
            resolver_context, test_path_spec, self._TEST_DATA
        )
        file_object.Open()

        text_reader = text_parser.EncodedTextReader(file_object)

        text_reader.ReadLines()
        self.assertEqual(text_reader.lines, self._TEST_LINES)

    def testSkipAhead(self):
        """Tests the SkipAhead function."""
        resolver_context = dfvfs_context.Context()

        test_path_spec = fake_path_spec.FakePathSpec(location="/file.txt")
        file_object = fake_file_io.FakeFile(
            resolver_context, test_path_spec, self._TEST_DATA
        )
        file_object.Open()

        text_reader = text_parser.EncodedTextReader(file_object)

        text_reader.SkipAhead(10)
        self.assertEqual(text_reader.lines, self._TEST_LINES[10:])

    def testReadLineUpdatesLinesSize(self):
        """Tests that ReadLine keeps lines_size in sync with the buffer."""
        # Newline-terminated so every line consumed by ReadLine includes its
        # newline, which makes lines_size == len(lines) hold exactly.
        test_data = b"\n".join([b"first line", b"second line", b"third line"])
        test_data = b"".join([test_data, b"\n"])

        resolver_context = dfvfs_context.Context()

        test_path_spec = fake_path_spec.FakePathSpec(location="/file.txt")
        file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, test_data)
        file_object.Open()

        text_reader = text_parser.EncodedTextReader(file_object)

        text_reader.ReadLines()
        while text_reader.lines:
            text_reader.ReadLine()
            self.assertEqual(text_reader.lines_size, len(text_reader.lines))

    def testReadLineReadsEntireLargeFile(self):
        """Tests that ReadLine reads a large file to its end.

        Regression test: a file larger than the read buffer, consumed
        line-by-line via ReadLine (the plugin reject path), must be read to
        its end. Inflating lines_size in ReadLine used to stall the refill in
        ReadLines and produce a false end-of-file.
        """
        number_of_lines = 25000
        test_data = b"\n".join([b"x" * 48] * number_of_lines) + b"\n"

        resolver_context = dfvfs_context.Context()

        test_path_spec = fake_path_spec.FakePathSpec(location="/file.txt")
        file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, test_data)
        file_object.Open()

        text_reader = text_parser.EncodedTextReader(file_object)

        number_of_read_lines = 0
        text_reader.ReadLines()
        while text_reader.lines:
            text_reader.ReadLine()
            text_reader.ReadLines()
            number_of_read_lines += 1

        self.assertEqual(number_of_read_lines, number_of_lines)
        self.assertEqual(text_reader.get_offset(), len(test_data))


class TextLogParserTest(test_lib.ParserTestCase):
    """Tests for the text log parser."""

    # pylint: disable=protected-access

    def testContainsBinary(self):
        """Tests the _ContainsBinary function."""
        parser = text_parser.TextLogParser()

        result = parser._ContainsBinary("this it text\n")
        self.assertFalse(result)

        result = parser._ContainsBinary("\x01\x00binary\x02\x00")
        self.assertTrue(result)

    def testEnablePlugins(self):
        """Tests the EnablePlugins function."""
        parser = text_parser.TextLogParser()

        number_of_plugins = len(parser._plugin_classes)

        parser.EnablePlugins([])
        self.assertEqual(len(parser._plugins_per_name), 0)

        parser.EnablePlugins(parser.ALL_PLUGINS)
        self.assertEqual(len(parser._plugins_per_name), number_of_plugins)

        parser.EnablePlugins(["apache_access"])
        self.assertEqual(len(parser._plugins_per_name), 1)

    def testParseFileObject(self):
        """Tests the ParseFileObject function."""
        text_parser.TextLogParser.RegisterPlugins([TestTextPlugin, OtherTestTextPlugin])

        try:
            parser = text_parser.TextLogParser()
            parser.EnablePlugins([TestTextPlugin.NAME, OtherTestTextPlugin.NAME])

            storage_writer = self._CreateStorageWriter()
            parser_mediator = self._CreateParserMediator(storage_writer)

            # Text that can be decoded is checked by every plugin.
            TestTextPlugin.checked_lines = []
            file_object = self._CreateFileObject("text.log", b"Text log line\n")

            with self.assertRaises(errors.WrongParser):
                parser.ParseFileObject(parser_mediator, file_object)

            self.assertEqual(
                TestTextPlugin.checked_lines,
                [
                    (TestTextPlugin.NAME, "Text log line\n"),
                    (OtherTestTextPlugin.NAME, "Text log line\n"),
                ],
            )

            # Data that cannot be decoded is not checked by any plugin.
            TestTextPlugin.checked_lines = []
            file_object = self._CreateFileObject("binary.log", b"Text\xff\xfelog\n")

            with self.assertRaises(errors.WrongParser):
                parser.ParseFileObject(parser_mediator, file_object)

            self.assertEqual(TestTextPlugin.checked_lines, [])

        finally:
            text_parser.TextLogParser.DeregisterPlugin(OtherTestTextPlugin)
            text_parser.TextLogParser.DeregisterPlugin(TestTextPlugin)


if __name__ == "__main__":
    unittest.main()
