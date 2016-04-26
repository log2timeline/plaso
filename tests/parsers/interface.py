#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the parsers and plugins interface classes."""

import unittest

from plaso.parsers import interface

from tests.parsers import test_lib


class BaseParserTest(test_lib.ParserTestCase):
  """Tests for the parser interface."""

  # pylint: disable=protected-access

  def testInitialize(self):
    """Tests the initialization."""
    parser_object = interface.BaseParser()

    self.assertIsNotNone(parser_object)
    self.assertIsNone(parser_object._default_plugin)
    self.assertEqual(parser_object._plugin_objects, [])

  def testSupportsPlugins(self):
    """Tests the SupportsPlugins function."""
    self.assertFalse(interface.BaseParser.SupportsPlugins())

  # The DeregisterPlugin and RegisterPlugin functions are tested in manager.py

  # The GetPluginObjectByName and GetPlugins functions are tested in manager.py


if __name__ == '__main__':
  unittest.main()
