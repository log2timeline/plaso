#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the log2timeline front-end."""

import unittest

from plaso.frontend import log2timeline
from plaso.frontend import test_lib


class Log2TimelineFrontendTest(test_lib.FrontendTestCase):
  """Tests for the log2timeline front-end."""

  def testGetPluginData(self):
    """Tests the GetPluginData function."""
    test_front_end = log2timeline.Log2TimelineFrontend()
    plugin_info = test_front_end.GetPluginData()

    self.assertIn(u'Hashers', plugin_info)
    available_hasher_names = []
    for hasher_info in plugin_info[u'Hashers']:
      available_hasher_names.append(hasher_info[0])
    self.assertIn(u'sha256', available_hasher_names)
    self.assertIn(u'sha1', available_hasher_names)

    self.assertIn(u'Parsers', plugin_info)
    self.assertIsNotNone(plugin_info[u'Parsers'])
    self.assertIn(u'Plugins', plugin_info)
    self.assertIsNotNone(plugin_info[u'Plugins'])

  # TODO: add GetTimeZones test.


if __name__ == '__main__':
  unittest.main()
