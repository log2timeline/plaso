#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the storage media tool object."""

import argparse
import unittest

from plaso.cli import storage_media_tool
from plaso.cli import test_lib
from plaso.lib import errors


class StorageMediaToolTest(test_lib.CLIToolTestCase):
  """Tests for the storage media tool object."""

  _EXPECTED_OUTPUT_STORAGE_MEDIA_OPTIONS = u'\n'.join([
      u'usage: storage_media_tool_test.py [--partition PARTITION_NUMBER]',
      u'                                  [-o IMAGE_OFFSET]',
      u'                                  [--sector_size BYTES_PER_SECTOR]',
      u'                                  [--ob IMAGE_OFFSET_BYTES]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --partition PARTITION_NUMBER',
      (u'                        Choose a partition number from a disk image. '
       u'This'),
      (u'                        partition number should correspond to the '
       u'partion'),
      (u'                        number on the disk image, starting from '
       u'partition 1.'),
      u'  -o IMAGE_OFFSET, --offset IMAGE_OFFSET',
      (u'                        The offset of the volume within the storage '
       u'media'),
      (u'                        image in number of sectors. A sector is 512 '
       u'bytes in'),
      (u'                        size by default this can be overwritten with '
       u'the'),
      u'                        --sector_size option.',
      u'  --sector_size BYTES_PER_SECTOR, --sector-size BYTES_PER_SECTOR',
      (u'                        The number of bytes per sector, which is 512 '
       u'by'),
      u'                        default.',
      (u'  --ob IMAGE_OFFSET_BYTES, --offset_bytes IMAGE_OFFSET_BYTES, '
       u'--offset_bytes IMAGE_OFFSET_BYTES'),
      (u'                        The offset of the volume within the storage '
       u'media'),
      u'                        image in number of bytes.',
      u''])

  _EXPECTED_OUTPUT_VSS_PROCESSING_OPTIONS = u'\n'.join([
      (u'usage: storage_media_tool_test.py [--no_vss] '
       u'[--vss_stores VSS_STORES]'),
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      (u'  --no_vss, --no-vss    Do not scan for Volume Shadow Snapshots '
       u'(VSS). This'),
      (u'                        means that VSS information will not be '
       u'included in the'),
      u'                        extraction phase.',
      u'  --vss_stores VSS_STORES, --vss-stores VSS_STORES',
      (u'                        Define Volume Shadow Snapshots (VSS) (or '
       u'stores that'),
      (u'                        need to be processed. A range of stores can '
       u'be defined'),
      (u'                        as: \'3..5\'. Multiple stores can be defined '
       u'as: \'1,3,5\''),
      (u'                        (a list of comma separated values). Ranges '
       u'and lists'),
      (u'                        can also be combined as: \'1,3..5\'. The '
       u'first store is'),
      u'                        1. All stores can be defined as: \'all\'.',
      u''])

  def testAddStorageMediaImageOptions(self):
    """Tests the AddStorageMediaImageOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'storage_media_tool_test.py',
        description=u'Test argument parser.',
        add_help=False)

    test_tool = storage_media_tool.StorageMediaTool()
    test_tool.AddStorageMediaImageOptions(argument_parser)

    output = argument_parser.format_help()
    self.assertEqual(output, self._EXPECTED_OUTPUT_STORAGE_MEDIA_OPTIONS)

  def testAddVssProcessingOptions(self):
    """Tests the AddVssProcessingOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'storage_media_tool_test.py',
        description=u'Test argument parser.',
        add_help=False)

    test_tool = storage_media_tool.StorageMediaTool()
    test_tool.AddVssProcessingOptions(argument_parser)

    output = argument_parser.format_help()
    self.assertEqual(output, self._EXPECTED_OUTPUT_VSS_PROCESSING_OPTIONS)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options.source = self._GetTestFilePath([u'ímynd.dd'])

    test_tool.ParseOptions(options)

    # TODO: improve this test.


if __name__ == '__main__':
  unittest.main()
