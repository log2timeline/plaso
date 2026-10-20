#!/usr/bin/env python3
"""Tests for the text plugins interface."""

import unittest

from plaso.lib import errors
from plaso.parsers.text_plugins import android_logcat
from plaso.parsers.text_plugins import dpkg
from plaso.parsers.text_plugins import postgresql

from tests.parsers import test_lib


class TextPluginTest(test_lib.ParserTestCase):
    """Tests for the text plugins interface."""

    # pylint: disable=protected-access

    # TODO: add tests for _GetMatchingLineStructure
    # TODO: add tests for _GetValueFromStructure
    # TODO: add tests for _ParseLines
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
            match = self._CheckEquivalentToScanString(plugin, line + line)
            self.assertIsNotNone(match)
            self.assertEqual(match[2], 0)

            # Match after leading whitespace or text on the first line. Note that
            # the PostgreSQL grammar requires the match to start at a line start.
            match = self._CheckEquivalentToScanString(plugin, "   " + line + line)
            match_after_text = self._CheckEquivalentToScanString(
                plugin, "bogus " + line
            )
            if plugin.NAME == "postgresql":
                self.assertIsNone(match)
                self.assertIsNone(match_after_text)
            else:
                self.assertIsNotNone(match)
                self.assertEqual(match[2], 3)
                self.assertIsNotNone(match_after_text)

            # Match at a line start after the first line.
            match = self._CheckEquivalentToScanString(plugin, "bogus " + line + line)
            if plugin.NAME == "postgresql":
                self.assertIsNone(match)

            # Match that only starts on a later line.
            match = self._CheckEquivalentToScanString(plugin, "bogus\n" + line)
            self.assertIsNone(match)

            # Match after a whitespace only first line.
            self._CheckEquivalentToScanString(plugin, "   \n" + line)

            # Match after an empty first line.
            self._CheckEquivalentToScanString(plugin, "\n" + line)

            # Tab on the first line.
            self._CheckEquivalentToScanString(plugin, "\t" + line)
            self._CheckEquivalentToScanString(plugin, line.replace(" ", "\t", 1))

            # No match.
            match = self._CheckEquivalentToScanString(plugin, "bogus\nbogus\n")
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
