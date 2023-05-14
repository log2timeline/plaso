#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the shared-cache strings (DSC) file parser."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.parsers.shared.unified_logging import dsc

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class DSCFileParserTest(test_lib.ParserTestCase):
  """Tests for the shared-cache strings (DSC) file parser parser."""

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    test_location = (
        '/private/var/db/uuidtext/dsc/BE7FE6AD45603AE2883E432F78B45062')

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

    parser = dsc.DSCFileParser()
    file_object = path_spec_resolver.Resolver.OpenFileObject(test_path_spec)
    dsc_file = parser.ParseFileObject(file_object)

    self.assertIsNotNone(dsc_file)
    self.assertEqual(len(dsc_file.ranges), 3491)
    self.assertEqual(len(dsc_file.uuids), 2274)


if __name__ == '__main__':
  unittest.main()
