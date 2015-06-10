#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the cookie plugins manager."""

import unittest

from plaso.parsers.cookie_plugins import interface
from plaso.parsers.cookie_plugins import manager


class TestCookiePlugin(interface.BaseCookiePlugin):
  """Test cookie plugin."""

  NAME = u'test_cookie_plugin'
  DESCRIPTION = u'Test cookie plugin.'

  def GetEntries(
      self, unused_parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extract and return EventObjects from the data structure.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      cookie_data: Optional cookie data, as a byte string. The default is None.
      url: Optional URL or path where the cookie got set. The default is None.
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
