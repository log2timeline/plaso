#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the plist parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import plist
# Register all plugins.
from plaso.parsers import plist_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


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

    parser.EnablePlugins(['airport'])
    self.assertEqual(len(parser._plugins_per_name), 1)

  def testParse(self):
    """Tests the Parse function."""
    parser = plist.PlistParser()
    storage_writer = self._ParseFile(['plist_binary'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 12)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseWithTruncatedFile(self):
    """Tests the Parse function on a truncated plist file."""
    parser = plist.PlistParser()

    with self.assertRaises(errors.WrongParser):
      self._ParseFile(['truncated.plist'], parser)

  def testParseWithXMLFileLeadingWhitespace(self):
    """Tests the Parse function on an XML file with leading whitespace."""
    parser = plist.PlistParser()
    storage_writer = self._ParseFile(['leading_whitespace.plist'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseWithXMLFileInvalidDate(self):
    """Tests the Parse function on an XML file with an invalid date and time."""
    parser = plist.PlistParser()
    storage_writer = self._ParseFile(['com.apple.security.KCN.plist'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseWithXMLFileExpatError(self):
    """Tests the Parse function on an XML file that causes an ExpatError."""
    parser = plist.PlistParser()

    with self.assertRaises(errors.WrongParser):
      self._ParseFile(['WMSDKNS.DTD'], parser)

  def testParseWithXMLFileBinASCIIError(self):
    """Tests the Parse function on an XML file that causes a binascii.Error."""
    parser = plist.PlistParser()

    with self.assertRaises(errors.WrongParser):
      self._ParseFile(['manageconsolidatedProviders.aspx.resx'], parser)

  def testParseWithXMLFileNoTopLevel(self):
    """Tests the Parse function on an XML file without top level."""
    parser = plist.PlistParser()

    with self.assertRaises(errors.WrongParser):
      test_path_segments = [
          'SettingsPane_{F8B5DB1C-D219-4bf9-A747-A1325024469B}'
          '.settingcontent-ms']
      self._ParseFile(test_path_segments, parser)

    # UTF-8 encoded XML file with byte-order-mark.
    with self.assertRaises(errors.WrongParser):
      self._ParseFile(['ReAgent.xml'], parser)

    # UTF-16 little-endian encoded XML file with byte-order-mark.
    with self.assertRaises(errors.WrongParser):
      self._ParseFile(['SampleMachineList.xml'], parser)

  def testParseWithXMLFileEncodingUnicode(self):
    """Tests the Parse function on an XML file with encoding Unicode."""
    parser = plist.PlistParser()

    with self.assertRaises(errors.WrongParser):
      self._ParseFile(['SAFStore.xml'], parser)

  def testParseWithEmptyBinaryPlistFile(self):
    """Tests the Parse function on an empty binary plist file."""
    parser = plist.PlistParser()
    storage_writer = self._ParseFile([
        'com.apple.networkextension.uuidcache.plist'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseWithXMLPlistFileNoTopLevel(self):
    """Tests the Parse function on an XML plist file without top level."""
    parser = plist.PlistParser()
    storage_writer = self._ParseFile(['empty.plist'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseWithXMLPlistFileEmptyTopLevel(self):
    """Tests the Parse function on an XML plist file with an empty top level."""
    parser = plist.PlistParser()
    storage_writer = self._ParseFile(['org.cups.printers.plist'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)


if __name__ == '__main__':
  unittest.main()
