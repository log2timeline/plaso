#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the parsers and plugins interface classes."""

import unittest

from plaso.parsers import interface

from tests.parsers import test_lib


class BaseParserTest(test_lib.ParserTestCase):
  """Tests for the parser interface."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = interface.BaseParser()

    parser.EnablePlugins([])
    self.assertEqual(len(parser._plugins_per_name), 0)

    parser.EnablePlugins(parser.ALL_PLUGINS)
    self.assertEqual(len(parser._plugins_per_name), 0)

  def testInitialize(self):
    """Tests the initialization."""
    parser = interface.BaseParser()

    self.assertIsNotNone(parser)
    self.assertIsNone(parser._default_plugin)
    self.assertEqual(parser._plugins_per_name, {})

  def testSupportsPlugins(self):
    """Tests the SupportsPlugins function."""
    self.assertFalse(interface.BaseParser.SupportsPlugins())

  # The DeregisterPlugin and RegisterPlugin functions are tested in manager.py

  # TODO: add tests for GetPluginNames
  # TODO: add tests for GetPluginObjectByName
  # TODO: add tests for GetPlugins


if __name__ == '__main__':
  unittest.main()
