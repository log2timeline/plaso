#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Bencode file parser."""

from __future__ import unicode_literals

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
    parser = bencode_parser.BencodeParser()
    parser.EnablePlugins(['bencode_transmission'])

    self.assertIsNotNone(parser)
    self.assertIsNone(parser._default_plugin)
    self.assertNotEqual(parser._plugins, [])
    self.assertEqual(len(parser._plugins), 1)


if __name__ == '__main__':
  unittest.main()
