#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the plist parser."""

import unittest

from plaso.parsers import plist
# Register all plugins.
from plaso.parsers import plist_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class PlistParserTest(test_lib.ParserTestCase):
  """Tests the plist parser."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser_object = plist.PlistParser()
    parser_object.EnablePlugins([u'airport'])

    self.assertIsNotNone(parser_object)
    self.assertIsNotNone(parser_object._default_plugin)
    self.assertNotEqual(parser_object._plugin_objects, [])
    self.assertEqual(len(parser_object._plugin_objects), 1)

  def testParse(self):
    """Tests the Parse function."""
    parser_object = plist.PlistParser()
    storage_writer = self._ParseFile(
        [u'plist_binary'], parser_object)

    self.assertEqual(len(storage_writer.events), 12)

    timestamps, roots, keys = zip(
        *[(evt.timestamp, evt.root, evt.key) for evt in storage_writer.events])

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
