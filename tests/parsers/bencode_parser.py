#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Bencode file parser."""

import unittest

from plaso.parsers import bencode_parser
from plaso.parsers import bencode_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class BencodeTest(test_lib.ParserTestCase):
  """Tests for the Bencode file parser."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = bencode_parser.BencodeParser()

    number_of_plugins = len(parser._plugin_classes)

    parser.EnablePlugins([])
    self.assertEqual(len(parser._plugins_per_name), 0)

    parser.EnablePlugins(parser.ALL_PLUGINS)
    self.assertEqual(len(parser._plugins_per_name), number_of_plugins)

    parser.EnablePlugins(['bencode_transmission'])
    self.assertEqual(len(parser._plugins_per_name), 1)


if __name__ == '__main__':
  unittest.main()
