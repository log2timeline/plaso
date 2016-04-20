#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the parsers and plugins interface classes."""

import unittest

from plaso.parsers import interface

from tests.parsers import test_lib


class BaseParserTest(test_lib.ParserTestCase):
  """Tests for the parser interface."""

  # pylint: disable=protected-access

  def testCheckForIntersection(self):
    """Tests the CheckForIntersection function."""
    includes = []
    excludes = []

    interface.BaseParser._CheckForIntersection(includes, excludes)
    self.assertEqual(includes, [])
    self.assertEqual(excludes, [])

    includes = [u'test_include']
    excludes = [u'test_exclude']

    interface.BaseParser._CheckForIntersection(includes, excludes)
    self.assertEqual(includes, [u'test_include'])
    self.assertEqual(excludes, [u'test_exclude'])

    includes = [u'test_include', u'test_intersection']
    excludes = [u'test_exclude', u'test_intersection']

    interface.BaseParser._CheckForIntersection(includes, excludes)
    self.assertEqual(includes, [u'test_include'])
    self.assertEqual(excludes, [u'test_exclude', u'test_intersection'])

  def testGetPluginFilters(self):
    """Tests the GetPluginFilters function."""
    plugin_filter_expression = u''
    includes, excludes = interface.BaseParser._GetPluginFilters(
        plugin_filter_expression)
    self.assertEqual(includes, [])
    self.assertEqual(excludes, [])

    plugin_filter_expression = u'test_include,!test_exclude'
    includes, excludes = interface.BaseParser._GetPluginFilters(
        plugin_filter_expression)
    self.assertEqual(includes, [u'test_include'])
    self.assertEqual(excludes, [u'test_exclude'])

    plugin_filter_expression = (
        u'test_include,test_intersection,!test_exclude,!test_intersection')
    includes, excludes = interface.BaseParser._GetPluginFilters(
        plugin_filter_expression)
    self.assertEqual(includes, [u'test_include'])
    self.assertEqual(excludes, [u'test_exclude', u'test_intersection'])

  def testSupportsPlugins(self):
    """Tests the SupportsPlugins function."""
    self.assertFalse(interface.BaseParser.SupportsPlugins())

  # The DeregisterPlugin and RegisterPlugin functions are tested in manager.py

  # The GetPluginNames, GetPluginObjectByName, GetPluginObjects and
  # GetPlugins functions are tested in manager.py


if __name__ == '__main__':
  unittest.main()
