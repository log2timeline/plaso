#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the log2timeline front-end."""

import unittest

from plaso.frontend import log2timeline

from tests.frontend import test_lib


class Log2TimelineFrontendTest(test_lib.FrontendTestCase):
  """Tests for the log2timeline front-end."""

  def testGetFiltersInformation(self):
    """Tests the _GetFiltersInformation function."""
    test_front_end = log2timeline.Log2TimelineFrontend()
    filters_info = test_front_end._GetFiltersInformation()

    self.assertIsNotNone(filters_info)

    available_filter_names = [name for name, _ in filters_info]
    self.assertIn(u'DynamicFilter', available_filter_names)
    self.assertIn(u'EventObjectFilter', available_filter_names)

  def testGetOutputModulesInformation(self):
    """Tests the _GetOutputModulesInformation function."""
    test_front_end = log2timeline.Log2TimelineFrontend()
    modules_info = test_front_end._GetOutputModulesInformation()

    self.assertIsNotNone(modules_info)

    available_module_names = [name for name, _ in modules_info]
    self.assertIn(u'dynamic', available_module_names)
    self.assertIn(u'json', available_module_names)

  def testGetDisabledOutputClasses(self):
    """Tests the GetDisabledOutputClasses function."""
    test_front_end = log2timeline.Log2TimelineFrontend()
    output_classes = list(test_front_end.GetDisabledOutputClasses())

    self.assertIsNotNone(output_classes)

  def testGetOutputClasses(self):
    """Tests the GetOutputClasses function."""
    test_front_end = log2timeline.Log2TimelineFrontend()
    output_classes = list(test_front_end.GetOutputClasses())

    self.assertIsNotNone(output_classes)

    available_output_names = [name for name, _ in output_classes]
    self.assertIn(u'dynamic', available_output_names)
    self.assertIn(u'json', available_output_names)

  def testGetPluginData(self):
    """Tests the GetPluginData function."""
    test_front_end = log2timeline.Log2TimelineFrontend()
    plugin_info = test_front_end.GetPluginData()

    self.assertIn(u'Hashers', plugin_info)

    available_hasher_names = [name for name, _ in plugin_info[u'Hashers']]
    self.assertIn(u'sha256', available_hasher_names)
    self.assertIn(u'sha1', available_hasher_names)

    self.assertIn(u'Parsers', plugin_info)
    self.assertIsNotNone(plugin_info[u'Parsers'])

    self.assertIn(u'Parser Plugins', plugin_info)
    self.assertIsNotNone(plugin_info[u'Parser Plugins'])


if __name__ == '__main__':
  unittest.main()
