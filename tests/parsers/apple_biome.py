#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple biome parser."""

import unittest

from plaso.parsers import apple_biome

from tests.parsers import test_lib


class AppleBiomeFileTest(test_lib.ParserTestCase):
  """Tests for the Apple biome file."""

  def testReadFileHeader(self):
    """Tests the _ReadFileHeader function."""
    biome_file = apple_biome.AppleBiomeFile()
    # pylint: disable=protected-access
    file_entry = self._GetTestFileEntry([
        'apple_biome', 'applaunch-segb-magfor'])
    file_object = file_entry.GetFileObject()

    header, header_size = biome_file._ReadFileHeader(file_object)

    self.assertEqual(header.segb_magic, b'SEGB')
    self.assertEqual(header.filename, b'690684028683239\x00')
    self.assertEqual(header_size, 56)

  def testOpen(self):
    """Tests the Open function."""
    biome_file = apple_biome.AppleBiomeFile()
    file_entry = self._GetTestFileEntry([
        'apple_biome', 'applaunch-segb-magfor'])
    file_object = file_entry.GetFileObject()

    biome_file.Open(file_object)

    self.assertEqual(biome_file.header.segb_magic, b'SEGB')
    self.assertEqual(biome_file.header.filename, b'690684028683239\x00')
    self.assertEqual(biome_file.records[0].size, 0x65)


class AppleBiomeParserTest(test_lib.ParserTestCase):
  """Apple Biome parser test case."""
  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    parser = apple_biome.AppleBiomeParser()

    storage_writer = self._ParseFile(
        ['apple_biome', 'applaunch-segb-magfor'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 558)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)


if __name__ == '__main__':
  unittest.main()
