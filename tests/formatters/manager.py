#!/usr/bin/env python3
"""Tests for the event formatters manager."""

import unittest

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.formatters import winreg

from tests import test_lib as shared_test_lib


class TestFormatterHelper1(interface.CustomEventFormatterHelper):
    """Custom event formatter helper for testing."""

    IDENTIFIER = "Test_Formatter_Helper1"

    def FormatEventValues(self, output_mediator, event_values):
        """Formats event values using the helper.

        Args:
          output_mediator (OutputMediator): output mediator.
          event_values (dict[str, object]): event values.
        """
        event_values["test"] = self.IDENTIFIER


class TestFormatterHelper2(TestFormatterHelper1):
    """Custom event formatter helper for testing."""

    IDENTIFIER = "test_formatter_helper2"


class FormattersManagerTest(shared_test_lib.BaseTestCase):
    """Tests for the event formatters manager."""

    # pylint: disable=protected-access

    def testGetEventFormatterHelper(self):
        """Tests the GetEventFormatterHelper function."""
        formatter_helper = manager.FormattersManager.GetEventFormatterHelper(
            "Windows_Registry_Values"
        )
        self.assertIsInstance(
            formatter_helper, winreg.WindowsRegistryValuesFormatterHelper
        )

        formatter_helper = manager.FormattersManager.GetEventFormatterHelper("bogus")
        self.assertIsNone(formatter_helper)

    def testRegisterEventFormatterHelper(self):
        """Tests the RegisterEventFormatterHelper function."""
        try:
            manager.FormattersManager.RegisterEventFormatterHelper(TestFormatterHelper1)

            formatter_helper = manager.FormattersManager.GetEventFormatterHelper(
                "test_formatter_helper1"
            )
            self.assertIsInstance(formatter_helper, TestFormatterHelper1)

            event_values = {}
            formatter_helper.FormatEventValues(None, event_values)
            self.assertEqual(event_values, {"test": "Test_Formatter_Helper1"})

            with self.assertRaises(KeyError):
                manager.FormattersManager.RegisterEventFormatterHelper(
                    TestFormatterHelper1
                )

        finally:
            manager.FormattersManager._custom_formatter_helpers.pop(
                "test_formatter_helper1", None
            )

    def testRegisterEventFormatterHelpers(self):
        """Tests the RegisterEventFormatterHelpers function."""
        try:
            manager.FormattersManager.RegisterEventFormatterHelpers(
                [TestFormatterHelper1, TestFormatterHelper2]
            )

            formatter_helper = manager.FormattersManager.GetEventFormatterHelper(
                "test_formatter_helper1"
            )
            self.assertIsNotNone(formatter_helper)
            self.assertEqual(formatter_helper.IDENTIFIER, "Test_Formatter_Helper1")

            formatter_helper = manager.FormattersManager.GetEventFormatterHelper(
                "test_formatter_helper2"
            )
            self.assertIsNotNone(formatter_helper)
            self.assertEqual(formatter_helper.IDENTIFIER, "test_formatter_helper2")

        finally:
            manager.FormattersManager._custom_formatter_helpers.pop(
                "test_formatter_helper1", None
            )
            manager.FormattersManager._custom_formatter_helpers.pop(
                "test_formatter_helper2", None
            )


if __name__ == "__main__":
    unittest.main()
