#!/usr/bin/env python3
"""Tests the plist parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import plist

# Register all plugins.
from plaso.parsers import plist_plugins  # pylint: disable=unused-import
from plaso.parsers.plist_plugins import interface

from tests.parsers import test_lib


class FailingFormatCheckPlugin(interface.PlistPlugin):
    """Plist plugin that fails its format check for testing."""

    NAME = "failing_format_check"
    DATA_FORMAT = "Test plist file"

    PLIST_KEYS = frozenset([])

    def CheckRequiredFormat(self, top_level):
        """Check if the plist has the minimal structure required by the plugin.

        Args:
          top_level (dict[str, object]): plist top-level item.

        Raises:
          RuntimeError: always.
        """
        raise RuntimeError("format check failed")

    # pylint: disable=arguments-differ
    def _ParsePlist(self, parser_mediator, top_level=None, **unused_kwargs):
        """Extracts entries for testing.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          top_level (Optional[dict[str, object]]): plist top-level item.
        """


class PlistParserTest(test_lib.ParserTestCase):
    """Tests the plist parser."""

    # pylint: disable=protected-access

    def testEnablePlugins(self):
        """Tests the EnablePlugins function."""
        parser = plist.PlistParser()

        number_of_plugins = len(parser._plugin_classes)

        parser.EnablePlugins([])
        self.assertEqual(len(parser._plugins_per_name), 0)

        parser.EnablePlugins(parser.ALL_PLUGINS)
        # Extract 1 for the default plugin.
        self.assertEqual(len(parser._plugins_per_name), number_of_plugins - 1)

        parser.EnablePlugins(["airport"])
        self.assertEqual(len(parser._plugins_per_name), 1)

    def testParse(self):
        """Tests the Parse function."""
        parser = plist.PlistParser()
        storage_writer = self._ParseFile(["plist", "com.apple.bluetooth.plist"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 6)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

    def testParseWithArrayTopLevel(self):
        """Tests the Parse function on a plist file with an array top level."""
        parser = plist.PlistParser()
        storage_writer = self._ParseFile(["plist", "InstallHistory.plist"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 7)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "data_type": "macos:install_history:entry",
            "name": "OS X",
            "process_name": "OS X Installer",
            "version": "10.9 (13A603)",
            "written_time": "2013-11-12T02:59:35.000000+00:00",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testParseWithPluginFormatCheckError(self):
        """Tests the Parse function with a plugin that fails its format check."""
        parser = plist.PlistParser()
        parser._plugins_per_name = {
            FailingFormatCheckPlugin.NAME: FailingFormatCheckPlugin()
        }
        storage_writer = self._ParseFile(["plist", "com.apple.bluetooth.plist"], parser)

        # The default plugin is used when no other plugin matches.
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 12)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

    def testParseWithTruncatedFile(self):
        """Tests the Parse function on a truncated plist file."""
        parser = plist.PlistParser()

        with self.assertRaises(errors.WrongParser):
            self._ParseFile(["plist", "truncated.plist"], parser)

    def testParseWithXMLFileLeadingWhitespace(self):
        """Tests the Parse function on an XML file with leading whitespace."""
        parser = plist.PlistParser()
        storage_writer = self._ParseFile(["plist", "leading_whitespace.plist"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

    def testParseWithXMLFileInvalidDate(self):
        """Tests the Parse function on an XML file with an invalid date and time."""
        parser = plist.PlistParser()
        storage_writer = self._ParseFile(
            ["plist", "com.apple.security.KCN.plist"], parser
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

    def testParseWithXMLFileExpatError(self):
        """Tests the Parse function on an XML file that causes an ExpatError."""
        parser = plist.PlistParser()

        with self.assertRaises(errors.WrongParser):
            self._ParseFile(["WMSDKNS.DTD"], parser)

    def testParseWithXMLFileBinASCIIError(self):
        """Tests the Parse function on an XML file that causes a binascii.Error."""
        parser = plist.PlistParser()

        with self.assertRaises(errors.WrongParser):
            self._ParseFile(["manageconsolidatedProviders.aspx.resx"], parser)

    def testParseWithXMLFileNoTopLevel(self):
        """Tests the Parse function on an XML file without top level."""
        parser = plist.PlistParser()

        with self.assertRaises(errors.WrongParser):
            test_path_segments = [
                "SettingsPane_{F8B5DB1C-D219-4bf9-A747-A1325024469B}"
                ".settingcontent-ms"
            ]
            self._ParseFile(test_path_segments, parser)

        # UTF-8 encoded XML file with byte-order-mark.
        with self.assertRaises(errors.WrongParser):
            self._ParseFile(["ReAgent.xml"], parser)

        # UTF-16 little-endian encoded XML file with byte-order-mark.
        with self.assertRaises(errors.WrongParser):
            self._ParseFile(["SampleMachineList.xml"], parser)

    def testParseWithXMLFileEncodingUnicode(self):
        """Tests the Parse function on an XML file with encoding Unicode."""
        parser = plist.PlistParser()

        with self.assertRaises(errors.WrongParser):
            self._ParseFile(["SAFStore.xml"], parser)

    def testParseWithEmptyBinaryPlistFile(self):
        """Tests the Parse function on an empty binary plist file."""
        parser = plist.PlistParser()
        storage_writer = self._ParseFile(
            ["plist", "com.apple.networkextension.uuidcache.plist"], parser
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

    def testParseWithXMLPlistFileNoTopLevel(self):
        """Tests the Parse function on an XML plist file without top level."""
        parser = plist.PlistParser()
        storage_writer = self._ParseFile(["plist", "empty.plist"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

    def testParseWithXMLPlistFileEmptyTopLevel(self):
        """Tests the Parse function on an XML plist file with an empty top level."""
        parser = plist.PlistParser()
        storage_writer = self._ParseFile(["plist", "org.cups.printers.plist"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)


if __name__ == "__main__":
    unittest.main()
