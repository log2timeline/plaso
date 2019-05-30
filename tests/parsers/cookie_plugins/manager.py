#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the cookie plugins manager."""

from __future__ import unicode_literals

import unittest

from plaso.parsers.cookie_plugins import interface
from plaso.parsers.cookie_plugins import manager


class TestCookiePlugin(interface.BaseCookiePlugin):
  """Test cookie plugin."""

  NAME = 'test_cookie_plugin'
  DESCRIPTION = 'Test cookie plugin.'

  # pylint: disable=unused-argument
  def GetEntries(self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extract and return EventObjects from the data structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      cookie_data (Optional[bytes]): cookie data, as a byte sequence.
      url (Optional[str]): URL or path where the cookie was set.
    """
    return


class CookiePluginsManagerTest(unittest.TestCase):
  """Tests for the cookie plugins manager."""

  def testPluginRegistration(self):
    """Tests the RegisterPlugin and DeregisterPlugin functions."""
    # pylint: disable=protected-access
    number_of_plugins = len(manager.CookiePluginsManager._plugin_classes)

    manager.CookiePluginsManager.RegisterPlugin(TestCookiePlugin)
    self.assertEqual(
        len(manager.CookiePluginsManager._plugin_classes),
        number_of_plugins + 1)

    with self.assertRaises(KeyError):
      manager.CookiePluginsManager.RegisterPlugin(TestCookiePlugin)

    manager.CookiePluginsManager.DeregisterPlugin(TestCookiePlugin)
    self.assertEqual(
        len(manager.CookiePluginsManager._plugin_classes),
        number_of_plugins)


if __name__ == '__main__':
  unittest.main()
