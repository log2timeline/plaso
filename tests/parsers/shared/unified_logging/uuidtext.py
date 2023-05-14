#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the uuidtext file parser."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.parsers.shared.unified_logging import uuidtext

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class UUIDTextFileParserTest(test_lib.ParserTestCase):
  """Tests for the uuidtext file parser parser."""

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    test_location = (
        '/private/var/db/uuidtext/25/73D0F065AB347881BF8906041310BA')

    test_file_path = os.path.join(
        shared_test_lib.TEST_DATA_PATH, 'unified_logging1.dmg')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_MODI, parent=test_path_spec)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GPT, location='/p1',
        parent=test_path_spec)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER,
        parent=test_path_spec, volume_index=0)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_location,
        parent=test_path_spec)

    parser = uuidtext.UUIDTextFileParser()
    file_object = path_spec_resolver.Resolver.OpenFileObject(test_path_spec)
    uuidtext_file = parser.ParseFileObject(file_object)

    self.assertIsNotNone(uuidtext_file)
    self.assertEqual(len(uuidtext_file.data), 4200)
    self.assertEqual(len(uuidtext_file.entries), 3)
    self.assertEqual(
        uuidtext_file.library_name, 'AppleThunderboltPCIDownAdapter')
    self.assertEqual(uuidtext_file.library_path, (
        '/System/Library/Extensions/AppleThunderboltPCIAdapters.kext/Contents/'
        'PlugIns/AppleThunderboltPCIDownAdapter.kext/Contents/MacOS/'
        'AppleThunderboltPCIDownAdapter'))


if __name__ == '__main__':
  unittest.main()
