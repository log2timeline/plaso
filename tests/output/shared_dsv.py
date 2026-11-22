#!/usr/bin/env python3
"""Tests for delimiter separated values shared output module."""

import io
import unittest

from plaso.output import dynamic
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


class DSVOutputModuleTest(test_lib.OutputModuleTestCase):
    """Tests the delimiter separated values shared output module."""

    # pylint: disable=protected-access

    def testSetFieldDelimiter(self):
        """Tests the SetFieldDelimiter function."""
        test_file_object = io.StringIO()

        output_mediator = self._CreateOutputMediator()

        output_module = shared_dsv.DSVOutputModule(
            dynamic.DynamicFieldFormattingHelper(), ["date", "time"]
        )
        output_module._file_object = test_file_object

        output_module.SetFieldDelimiter("|")
        output_module.WriteHeader(output_mediator)

        header = test_file_object.getvalue()
        self.assertEqual(header, "date|time\n")

    def testSetFields(self):
        """Tests the SetFields function."""
        test_file_object = io.StringIO()

        output_mediator = self._CreateOutputMediator()

        output_module = shared_dsv.DSVOutputModule(
            dynamic.DynamicFieldFormattingHelper(), ["date", "time"]
        )
        output_module._file_object = test_file_object

        output_module.SetFields(["hostname", "date", "username"])
        output_module.WriteHeader(output_mediator)

        header = test_file_object.getvalue()
        self.assertEqual(header, "hostname,date,username\n")


if __name__ == "__main__":
    unittest.main()
