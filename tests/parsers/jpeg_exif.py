#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the JPEG EXIF parser."""

import unittest

from plaso.parsers import jpeg_exif

from tests.parsers import test_lib


class JpegExifParserTest(test_lib.ParserTestCase):
  """Tests for the JPEG EXIF parser."""

  def testParseFile(self):
    """Tests the ParseFile function on a JPEG file."""
    parser = jpeg_exif.JpegExifParser()
    storage_writer = self._ParseFile(['testimage.jpg'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        "bodyserialnumber": "53HQK520M10K6U",
        "data_type": "jpeg:exif",
        "latitude": "68.87571N",
        "longitude": "27.76492E",
        "manufacturer": "DJI",
        "model": "FC3582",
        "software": "RawTherapee 5.9",
        "width": "4024",
        "height": "3016",
        "xres": "300.0",
        "yres": "300.0"}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    print(str(event_data.__dict__))
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
