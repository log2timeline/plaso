#!/usr/bin/env python3
"""Tests for delimiter separated values shared output module."""

import unittest

from plaso.output import shared_dsv

from tests.output import test_lib


class DSVEventFormattingHelperTest(test_lib.OutputModuleTestCase):
    """Tests the delimiter separated values event formatting helper."""

    # pylint: disable=protected-access

    def testSanitizeField(self):
        """Tests the _SanitizeField function."""
        formatting_helper = shared_dsv.DSVEventFormattingHelper(None, ["field"])

        # A field delimiter is replaced with a space.
        sanitized_field = formatting_helper._SanitizeField("a,b")
        self.assertEqual(sanitized_field, "a b")

        # A carriage return or newline is replaced with a space so that a single
        # event cannot be split over multiple rows.
        sanitized_field = formatting_helper._SanitizeField("a\nb")
        self.assertEqual(sanitized_field, "a b")

        sanitized_field = formatting_helper._SanitizeField("a\r\nb")
        self.assertEqual(sanitized_field, "a  b")

        # A value that a spreadsheet application would read as a formula is
        # neutralized by prefixing it with an apostrophe.
        sanitized_field = formatting_helper._SanitizeField("=1+1")
        self.assertEqual(sanitized_field, "'=1+1")

        sanitized_field = formatting_helper._SanitizeField("+1")
        self.assertEqual(sanitized_field, "'+1")

        sanitized_field = formatting_helper._SanitizeField("-1+2")
        self.assertEqual(sanitized_field, "'-1+2")

        sanitized_field = formatting_helper._SanitizeField("@SUM(A1)")
        self.assertEqual(sanitized_field, "'@SUM(A1)")

        # Values that need no neutralization are left unchanged.
        sanitized_field = formatting_helper._SanitizeField("plain")
        self.assertEqual(sanitized_field, "plain")

        # The single character placeholder for an empty field is not a formula
        # and is left unchanged.
        sanitized_field = formatting_helper._SanitizeField("-")
        self.assertEqual(sanitized_field, "-")

        # A value that contains a double quote is enclosed in double quotes and
        # the double quote is escaped with another double quote.
        sanitized_field = formatting_helper._SanitizeField('a"b')
        self.assertEqual(sanitized_field, '"a""b"')

        sanitized_field = formatting_helper._SanitizeField('"quoted", value')
        self.assertEqual(sanitized_field, '"""quoted""  value"')

        sanitized_field = formatting_helper._SanitizeField('=1+"1"')
        self.assertEqual(sanitized_field, '"\'=1+""1"""')

        # A value that contains a single quote is not enclosed in double quotes.
        sanitized_field = formatting_helper._SanitizeField("it's")
        self.assertEqual(sanitized_field, "it's")

        # A value that contains a double quote is left unchanged when quoting is
        # disabled.
        formatting_helper = shared_dsv.DSVEventFormattingHelper(
            None, ["field"], field_delimiter="|", quote_fields=False
        )

        sanitized_field = formatting_helper._SanitizeField('a"b')
        self.assertEqual(sanitized_field, 'a"b')


class DSVOutputModuleTest(test_lib.OutputModuleTestCase):
    """Tests the delimiter separated values shared output module."""

    # TODO: add coverage for SetFieldDelimiter
    # TODO: add coverage for SetFields


if __name__ == "__main__":
    unittest.main()
