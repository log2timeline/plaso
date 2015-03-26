#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry file parser."""

import unittest

from plaso.parsers import test_lib
from plaso.parsers import winreg


class WinRegTest(test_lib.ParserTestCase):
  """Tests for the Windows Registry file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = winreg.WinRegistryParser()

  def _GetParserChains(self, event_objects):
    """Return a dict with a plugin count given a list of event objects."""
    parser_chains = {}
    for event_object in event_objects:
      parser_chain = getattr(event_object, 'parser', None)
      if not parser_chain:
        continue

      if parser_chain in parser_chains:
        parser_chains[parser_chain] += 1
      else:
        parser_chains[parser_chain] = 1

    return parser_chains

  def _PluginNameToParserChain(self, plugin_name):
    """Generate the correct parser chain for a given plugin."""
    return 'winreg/{0:s}'.format(plugin_name)

  def testNtuserParsing(self):
    """Parse a NTUSER.dat file and check few items."""
    knowledge_base_values = {'current_control_set': u'ControlSet001'}
    test_file = self._GetTestFilePath(['NTUSER.DAT'])
    event_queue_consumer = self._ParseFile(
        self._parser, test_file, knowledge_base_values=knowledge_base_values)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    parser_chains = self._GetParserChains(event_objects)

    # The _registry_type member is created dynamically by invoking
    # the _GetParserChains function.
    registry_type = getattr(self._parser, '_registry_type', '')
    self.assertEqual(registry_type, 'NTUSER')

    expected_chain = self._PluginNameToParserChain('winreg_userassist')
    self.assertTrue(expected_chain in parser_chains)

    self.assertEqual(parser_chains[expected_chain], 14)

  def testSystemParsing(self):
    """Parse a SYSTEM hive an run few tests."""
    knowledge_base_values = {'current_control_set': u'ControlSet001'}
    test_file = self._GetTestFilePath(['SYSTEM'])
    event_queue_consumer = self._ParseFile(
        self._parser, test_file, knowledge_base_values=knowledge_base_values)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    parser_chains = self._GetParserChains(event_objects)

    # The _registry_type member is created dynamically by invoking
    # the _GetParserChains function.
    registry_type = getattr(self._parser, '_registry_type', '')
    self.assertEqual(registry_type, 'SYSTEM')

    # Check the existence of few known plugins, see if they
    # are being properly picked up and are parsed.
    plugin_names = ['winreg_usbstor', 'winreg_boot_execute', 'winreg_services']
    for plugin in plugin_names:
      expected_chain = self._PluginNameToParserChain(plugin)
      self.assertTrue(
          expected_chain in parser_chains,
          u'Chain {0:s} not found in events.'.format(expected_chain))

    # Check that the number of events produced by each plugin are correct.
    self.assertEqual(parser_chains.get(
        self._PluginNameToParserChain('winreg_usbstor'), 0), 3)
    self.assertEqual(parser_chains.get(
        self._PluginNameToParserChain('winreg_boot_execute'), 0), 2)
    self.assertEqual(parser_chains.get(
        self._PluginNameToParserChain('winreg_services'), 0), 831)


if __name__ == '__main__':
  unittest.main()
