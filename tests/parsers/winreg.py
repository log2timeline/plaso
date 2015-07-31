#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry file parser."""

import unittest

from plaso.parsers import winreg
from plaso.winregistry import regf

from tests.parsers import test_lib


class WinRegTest(test_lib.ParserTestCase):
  """Tests for the Windows Registry file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = winreg.WinRegistryParser()

  def _GetParserChains(self, event_objects):
    """Return a dict with a plugin count given a list of event objects."""
    parser_chains = {}
    for event_object in event_objects:
      parser_chain = getattr(event_object, u'parser', None)
      if not parser_chain:
        continue

      if parser_chain in parser_chains:
        parser_chains[parser_chain] += 1
      else:
        parser_chains[parser_chain] = 1

    return parser_chains

  def _OpenWinRegFile(self, filename):
    """Opens a Windows Registry file.

    Args:
      filename: The filename of the Windows Registry file, relative to
                the test data location.

    Returns:
      A Windows Registry file object (instance of WinRegFile).
    """
    file_entry = self._GetTestFileEntryFromPath([filename])
    winreg_file = regf.WinPyregfFile()
    winreg_file.OpenFileEntry(file_entry)

    return winreg_file

  def _PluginNameToParserChain(self, plugin_name):
    """Generate the correct parser chain for a given plugin."""
    return u'winreg/{0:s}'.format(plugin_name)

  def testGetRegistryFileType(self):
    """Tests the _GetRegistryFileType function."""
    winreg_file = self._OpenWinRegFile(u'NTUSER.DAT')

    registry_type = self._parser._GetRegistryFileType(winreg_file)
    self.assertEqual(registry_type, u'NTUSER')

    winreg_file.Close()

    winreg_file = self._OpenWinRegFile(u'SYSTEM')

    registry_type = self._parser._GetRegistryFileType(winreg_file)
    self.assertEqual(registry_type, u'SYSTEM')

    winreg_file.Close()

  def testParseNTUserDat(self):
    """Tests the Parse function on a NTUSER.DAT file."""
    knowledge_base_values = {u'current_control_set': u'ControlSet001'}
    test_file = self._GetTestFilePath([u'NTUSER.DAT'])
    event_queue_consumer = self._ParseFile(
        self._parser, test_file, knowledge_base_values=knowledge_base_values)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    parser_chains = self._GetParserChains(event_objects)

    expected_chain = self._PluginNameToParserChain(u'userassist')
    self.assertTrue(expected_chain in parser_chains)

    self.assertEqual(parser_chains[expected_chain], 14)

  def testParseSystem(self):
    """Tests the Parse function on a SYSTEM file."""
    knowledge_base_values = {u'current_control_set': u'ControlSet001'}
    test_file = self._GetTestFilePath([u'SYSTEM'])
    event_queue_consumer = self._ParseFile(
        self._parser, test_file, knowledge_base_values=knowledge_base_values)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    parser_chains = self._GetParserChains(event_objects)

    # Check the existence of few known plugins, see if they
    # are being properly picked up and are parsed.
    plugin_names = [
        u'windows_usbstor_devices', u'windows_boot_execute',
        u'windows_services']
    for plugin in plugin_names:
      expected_chain = self._PluginNameToParserChain(plugin)
      self.assertTrue(
          expected_chain in parser_chains,
          u'Chain {0:s} not found in events.'.format(expected_chain))

    # Check that the number of events produced by each plugin are correct.
    self.assertEqual(parser_chains.get(
        self._PluginNameToParserChain(u'windows_usbstor_devices'), 0), 3)
    self.assertEqual(parser_chains.get(
        self._PluginNameToParserChain(u'windows_boot_execute'), 0), 2)
    self.assertEqual(parser_chains.get(
        self._PluginNameToParserChain(u'windows_services'), 0), 831)


if __name__ == '__main__':
  unittest.main()
