"""MSIE zone settings custom event formatter helpers."""

from plaso.formatters import interface
from plaso.formatters import manager


class MSIEZoneSettingsFormatterHelper(interface.CustomEventFormatterHelper):
    """MSIE zone settings formatter helper."""

    IDENTIFIER = "msie_zone_settings"

    _CONTROL_VALUES_1A00 = {
        0x00000000: (
            "0x00000000 (Automatic logon with current user name and password)"
        ),
        0x00010000: "0x00010000 (Prompt for user name and password)",
        0x00020000: "0x00020000 (Automatic logon only in Intranet zone)",
        0x00030000: "0x00030000 (Anonymous logon)",
    }

    _CONTROL_VALUES_1C00 = {
        0x00000000: "0x00000000 (Disable Java)",
        0x00010000: "0x00010000 (High safety)",
        0x00020000: "0x00020000 (Medium safety)",
        0x00030000: "0x00030000 (Low safety)",
        0x00800000: "0x00800000 (Custom)",
    }

    _CONTROL_VALUES_PERMISSIONS = {
        0x00000000: "0 (Allow)",
        0x00000001: "1 (Prompt User)",
        0x00000003: "3 (Not Allowed)",
        0x00010000: "0x00010000 (Administrator approved)",
    }

    _CONTROL_VALUES_SAFETY = {
        0x00010000: "0x00010000 (High safety)",
        0x00020000: "0x00020000 (Medium safety)",
        0x00030000: "0x00030000 (Low safety)",
    }

    _KNOWN_FEATURE_CONTROLS = {
        "1200": "Run ActiveX controls and plug-ins",
        "1400": "Active scripting",
        "1001": "Download signed ActiveX controls",
        "1004": "Download unsigned ActiveX controls",
        "1201": "Initialize and script ActiveX controls not marked as safe",
        "1206": "Allow scripting of IE Web browser control",
        "1207": "Reserved",
        "1208": "Allow previously unused ActiveX controls to run without prompt",
        "1209": "Allow Scriptlets",
        "120A": "Override Per-Site (domain-based) ActiveX restrictions",
        "120B": "Override Per-Site (domain-based) ActiveX restrictions",
        "1402": "Scripting of Java applets",
        "1405": "Script ActiveX controls marked as safe for scripting",
        "1406": "Access data sources across domains",
        "1407": "Allow Programmatic clipboard access",
        "1408": "Reserved",
        "1601": "Submit non-encrypted form data",
        "1604": "Font download",
        "1605": "Run Java",
        "1606": "Userdata persistence",
        "1607": "Navigate sub-frames across different domains",
        "1608": "Allow META REFRESH",
        "1609": "Display mixed content",
        "160A": "Include local directory path when uploading files to a server",
        "1800": "Installation of desktop items",
        "1802": "Drag and drop or copy and paste files",
        "1803": "File Download",
        "1804": "Launching programs and files in an IFRAME",
        "1805": "Launching programs and files in webview",
        "1806": "Launching applications and unsafe files",
        "1807": "Reserved",
        "1808": "Reserved",
        "1809": "Use Pop-up Blocker",
        "180A": "Reserved",
        "180B": "Reserved",
        "180C": "Reserved",
        "180D": "Reserved",
        "1A00": "User Authentication: Logon",
        "1A02": "Allow persistent cookies that are stored on your computer",
        "1A03": "Allow per-session cookies (not stored)",
        "1A04": "Don't prompt for client cert selection when no certs exists",
        "1A05": "Allow 3rd party persistent cookies",
        "1A06": "Allow 3rd party session cookies",
        "1A10": "Privacy Settings",
        "1C00": "Java permissions",
        "1E05": "Software channel permissions",
        "1F00": "Reserved",
        "2000": "Binary and script behaviors",
        "2001": ".NET: Run components signed with Authenticode",
        "2004": ".NET: Run components not signed with Authenticode",
        "2100": "Open files based on content, not file extension",
        "2101": "Web sites in less privileged zone can navigate into this zone",
        "2102": "Allow script initiated windows without size/position constraints",
        "2103": "Allow status bar updates via script",
        "2104": "Allow websites to open windows without address or status bars",
        "2105": "Allow websites to prompt for information using scripted windows",
        "2200": "Automatic prompting for file downloads",
        "2201": "Automatic prompting for ActiveX controls",
        "2300": "Allow web pages to use restricted protocols for active content",
        "2301": "Use Phishing Filter",
        "2400": ".NET: XAML browser applications",
        "2401": ".NET: XPS documents",
        "2402": ".NET: Loose XAML",
        "2500": "Turn on Protected Mode",
        "2600": "Enable .NET Framework setup",
        "{AEBA21FA-782A-4A90-978D-B72164C80120}": "First Party Cookie",
        "{A8A88C49-5EB2-4990-A1A2-0876022C854F}": "Third Party Cookie",
    }

    _KNOWN_PERMISSIONS_SETTINGS = frozenset(
        [
            "1001",
            "1004",
            "1200",
            "1201",
            "1400",
            "1402",
            "1405",
            "1406",
            "1407",
            "1601",
            "1604",
            "1606",
            "1607",
            "1608",
            "1609",
            "1800",
            "1802",
            "1803",
            "1804",
            "1809",
            "1A04",
            "2000",
            "2001",
            "2004",
            "2100",
            "2101",
            "2102",
            "2200",
            "2201",
            "2300",
        ]
    )

    def FormatEventValues(self, output_mediator, event_values):
        """Formats event values using the helper.

        Args:
          output_mediator (OutputMediator): output mediator.
          event_values (dict[str, object]): event values.
        """
        settings = event_values.get("settings") or []
        if isinstance(settings, str):
            return

        string_parts = []
        for key, value in event_values.get("settings") or []:
            if isinstance(value, int):
                if key in self._KNOWN_PERMISSIONS_SETTINGS:
                    value = self._CONTROL_VALUES_PERMISSIONS.get(value, value)
                elif key == "1A00":
                    value = self._CONTROL_VALUES_1A00.get(value, value)
                elif key == "1C00":
                    value = self._CONTROL_VALUES_1C00.get(value, value)
                elif key == "1E05":
                    value = self._CONTROL_VALUES_SAFETY.get(value, value)

            if len(key) == 4 and key != "Icon":
                value_description = self._KNOWN_FEATURE_CONTROLS.get(key, "UNKNOWN")
            else:
                value_description = self._KNOWN_FEATURE_CONTROLS.get(key)

            if value_description:
                feature_control = f"[{key:s}] {value_description:s}: {value!s}"
            else:
                feature_control = f"[{key:s}]: {value!s}"

            string_parts.append(feature_control)

        event_values["settings"] = ", ".join(string_parts)


manager.FormattersManager.RegisterEventFormatterHelper(MSIEZoneSettingsFormatterHelper)
