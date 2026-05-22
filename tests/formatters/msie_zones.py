#!/usr/bin/env python3
"""Tests for the Windows Registry custom event formatter helpers."""

import unittest

from plaso.formatters import msie_zones

from tests.formatters import test_lib


class MSIEZoneSettingsFormatterHelperTest(test_lib.EventFormatterTestCase):
    """Tests for the MSIE zone settings formatter helper."""

    def testFormatEventValues(self):
        """Tests the FormatEventValues function."""
        formatter_helper = msie_zones.MSIEZoneSettingsFormatterHelper()

        output_mediator = self._CreateOutputMediator()

        event_values = {
            "settings": [
                ("1200", 0),
                ("1400", 1),
                ("1402", 3),
                ("1407", 0x00010000),
                ("1A00", 0x00030000),
                ("1C00", 0x00020000),
                ("1E05", 0x00030000),
                ("2200", 2),
                ("9999", 0),
                ("Flags", 33),
                ("Icon", "shell32.dll#0016"),
                ("PMDisplayName", "Computer [Protected Mode]"),
            ]
        }
        formatter_helper.FormatEventValues(output_mediator, event_values)

        expected_settings = [
            "[1200] Run ActiveX controls and plug-ins: 0 (Allow)",
            "[1400] Active scripting: 1 (Prompt User)",
            "[1402] Scripting of Java applets: 3 (Not Allowed)",
            (
                "[1407] Allow Programmatic clipboard access: 0x00010000 "
                "(Administrator approved)"
            ),
            "[1A00] User Authentication: Logon: 0x00030000 (Anonymous logon)",
            "[1C00] Java permissions: 0x00020000 (Medium safety)",
            "[1E05] Software channel permissions: 0x00030000 (Low safety)",
            "[2200] Automatic prompting for file downloads: 2",
            "[9999] UNKNOWN: 0",
            "[Flags]: 33",
            "[Icon]: shell32.dll#0016",
            "[PMDisplayName]: Computer [Protected Mode]",
        ]
        # pylint: disable=no-member
        self.assertEqual(event_values["settings"].split(", "), expected_settings)

        event_values = {"settings": "[Flags]: 33, [Icon]: shell32.dll#0016"}
        formatter_helper.FormatEventValues(output_mediator, event_values)
        self.assertEqual(
            event_values["settings"], "[Flags]: 33, [Icon]: shell32.dll#0016"
        )

        event_values = {"settings": None}
        formatter_helper.FormatEventValues(output_mediator, event_values)
        self.assertEqual(event_values["settings"], "")


if __name__ == "__main__":
    unittest.main()
