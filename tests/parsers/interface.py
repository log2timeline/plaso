#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the parsers and plugins interface classes."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import interface

from tests.parsers import test_lib


class BaseParserTest(test_lib.ParserTestCase):
  """Tests for the parser interface."""

  # pylint: disable=protected-access

  def testInitialize(self):
    """Tests the initialization."""
    parser = interface.BaseParser()

    self.assertIsNotNone(parser)
    self.assertIsNone(parser._default_plugin)
    self.assertEqual(parser._plugins, [])

  def testSupportsPlugins(self):
    """Tests the SupportsPlugins function."""
    self.assertFalse(interface.BaseParser.SupportsPlugins())

  # The DeregisterPlugin and RegisterPlugin functions are tested in manager.py

  # The GetPluginObjectByName and GetPlugins functions are tested in manager.py


if __name__ == '__main__':
  unittest.main()
