#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the compound ZIP archive parser."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import czip
# Register all plugins.
from plaso.parsers import czip_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class CompoundZIPTest(test_lib.ParserTestCase):
  """Tests for the compound ZIP archive parser."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = czip.CompoundZIPParser()
    parser.EnablePlugins(['oxml'])

    self.assertIsNotNone(parser)
    self.assertIsNone(parser._default_plugin)
    self.assertNotEqual(parser._plugins, [])
    self.assertEqual(len(parser._plugins), 1)


if __name__ == '__main__':
  unittest.main()
