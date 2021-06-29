#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the compound ZIP archive parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import czip
from plaso.parsers import czip_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class CompoundZIPTest(test_lib.ParserTestCase):
  """Tests for the compound ZIP archive parser."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = czip.CompoundZIPParser()

    number_of_plugins = len(parser._plugin_classes)

    parser.EnablePlugins([])
    self.assertEqual(len(parser._plugins), 0)

    parser.EnablePlugins(parser.ALL_PLUGINS)
    self.assertEqual(len(parser._plugins), number_of_plugins)

    parser.EnablePlugins(['oxml'])
    self.assertEqual(len(parser._plugins), 1)

  def testParse(self):
    """Tests the Parse function."""
    parser = czip.CompoundZIPParser()
    storage_writer = self._ParseFile(['syslog.zip'], parser)

    self.assertEqual(storage_writer.number_of_events, 0)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    # Try parsing a file that is not a ZIP file.
    parser = czip.CompoundZIPParser()

    with self.assertRaises(errors.UnableToParseFile):
      storage_writer = self._ParseFile(['syslog.xz'], parser)

    # Try parsing a file that is not a ZIP file but looks like one.
    parser = czip.CompoundZIPParser()

    with self.assertRaises(errors.UnableToParseFile):
      storage_writer = self._ParseFile(['passes_is_zipfile.bin'], parser)


if __name__ == '__main__':
  unittest.main()
