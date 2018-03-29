#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry file parser."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import winreg
# Register all plugins.
from plaso.parsers import winreg_plugins  # pylint: disable=unused-import

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class WinRegistryParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Registry file parser."""

  # pylint: disable=protected-access

  def _GetParserChains(self, events):
    """Return a dict with a plugin count given a list of events."""
    parser_chains = {}
    for event in events:
      parser_chain = getattr(event, 'parser', None)
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

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = winreg.WinRegistryParser()
    parser.EnablePlugins(['appcompatcache'])

    self.assertIsNotNone(parser)
    self.assertIsNotNone(parser._default_plugin)
    self.assertNotEqual(parser._plugins, [])
    self.assertEqual(len(parser._plugins), 1)

  @shared_test_lib.skipUnlessHasTestFile(['NTUSER.DAT'])
  def testParseNTUserDat(self):
    """Tests the Parse function on a NTUSER.DAT file."""
    parser = winreg.WinRegistryParser()
    storage_writer = self._ParseFile(['NTUSER.DAT'], parser)

    events = list(storage_writer.GetEvents())

    parser_chains = self._GetParserChains(events)

    expected_parser_chain = self._PluginNameToParserChain('userassist')
    self.assertTrue(expected_parser_chain in parser_chains)

    self.assertEqual(parser_chains[expected_parser_chain], 14)

  @shared_test_lib.skipUnlessHasTestFile(['ntuser.dat.LOG'])
  def testParseNoRootKey(self):
    """Test the parse function on a Registry file with no root key."""
    parser = winreg.WinRegistryParser()
    storage_writer = self._ParseFile(['ntuser.dat.LOG'], parser)

    self.assertEqual(storage_writer.number_of_events, 0)

  @shared_test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testParseSystem(self):
    """Tests the Parse function on a SYSTEM file."""
    parser = winreg.WinRegistryParser()
    storage_writer = self._ParseFile(['SYSTEM'], parser)

    events = list(storage_writer.GetEvents())

    parser_chains = self._GetParserChains(events)

    # Check the existence of few known plugins, see if they
    # are being properly picked up and are parsed.
    plugin_names = [
        'windows_usbstor_devices', 'windows_boot_execute',
        'windows_services']
    for plugin in plugin_names:
      expected_parser_chain = self._PluginNameToParserChain(plugin)
      self.assertTrue(
          expected_parser_chain in parser_chains,
          'Chain {0:s} not found in events.'.format(expected_parser_chain))

    # Check that the number of events produced by each plugin are correct.
    parser_chain = self._PluginNameToParserChain('windows_usbstor_devices')
    self.assertEqual(parser_chains.get(parser_chain, 0), 10)

    parser_chain = self._PluginNameToParserChain('windows_boot_execute')
    self.assertEqual(parser_chains.get(parser_chain, 0), 4)

    parser_chain = self._PluginNameToParserChain('windows_services')
    self.assertEqual(parser_chains.get(parser_chain, 0), 831)


if __name__ == '__main__':
  unittest.main()
