#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Bencode file parser."""

import unittest

from plaso.parsers import bencode_parser
# Register all plugins.
from plaso.parsers import bencode_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class BencodeTest(test_lib.ParserTestCase):
  """Tests for the Bencode file parser."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser_object = bencode_parser.BencodeParser()
    parser_object.EnablePlugins([u'bencode_transmission'])

    self.assertIsNotNone(parser_object)
    self.assertIsNone(parser_object._default_plugin)
    self.assertNotEqual(parser_object._plugin_objects, [])
    self.assertEqual(len(parser_object._plugin_objects), 1)


if __name__ == '__main__':
  unittest.main()
