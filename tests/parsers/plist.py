#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the plist parser."""

import unittest

from plaso.parsers import plist
# Register all plugins.
from plaso.parsers import plist_plugins  # pylint: disable=unused-import

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class PlistParserTest(test_lib.ParserTestCase):
  """Tests the plist parser."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = plist.PlistParser()
    parser.EnablePlugins([u'airport'])

    self.assertIsNotNone(parser)
    self.assertIsNotNone(parser._default_plugin)
    self.assertNotEqual(parser._plugins, [])
    self.assertEqual(len(parser._plugins), 1)

  @shared_test_lib.skipUnlessHasTestFile([u'plist_binary'])
  def testParse(self):
    """Tests the Parse function."""
    parser = plist.PlistParser()
    storage_writer = self._ParseFile([u'plist_binary'], parser)

    self.assertEqual(storage_writer.number_of_events, 12)

    timestamps, roots, keys = zip(
        *[(event.timestamp, event.root, event.key)
          for event in storage_writer.GetEvents()])

    expected_timestamps = frozenset([
        1345251192528750, 1351827808261762, 1345251268370453,
        1351818803000000, 1351819298997672, 1351818797324095,
        1301012201414766, 1302199013524275, 1341957900020116,
        1350666391557044, 1350666385239661, 1341957896010535])

    self.assertTrue(set(expected_timestamps) == set(timestamps))
    self.assertEqual(12, len(set(timestamps)))

    expected_roots = frozenset([
        u'/DeviceCache/00-0d-fd-00-00-00',
        u'/DeviceCache/44-00-00-00-00-00',
        u'/DeviceCache/44-00-00-00-00-01',
        u'/DeviceCache/44-00-00-00-00-02',
        u'/DeviceCache/44-00-00-00-00-03',
        u'/DeviceCache/44-00-00-00-00-04'])
    self.assertTrue(expected_roots == set(roots))
    self.assertEqual(6, len(set(roots)))

    expected_keys = frozenset([
        u'LastInquiryUpdate',
        u'LastServicesUpdate',
        u'LastNameUpdate'])
    self.assertTrue(expected_keys == set(keys))
    self.assertEqual(3, len(set(keys)))


if __name__ == '__main__':
  unittest.main()
