#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the DJI Drone parser."""

import unittest

from plaso.parsers import dji_mavic

from tests.parsers import test_lib


class DJIDroneLogParserTest(test_lib.ParserTestCase):
  """Tests for the DJI Drone parser."""

  def testParseFile(self):
    """Tests the Parse function on a Dji Drone DAT file."""
    parser = dji_mavic.DJIDroneLogParser()
    storage_writer = self._ParseFile(['17-08-29-12-58-45_FLY005.DAT'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1786)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'longitude': -106.2163995, 
        'latitude': 39.9612155,
        'data_type': 'drone:dji:mavic',
        'timestamp': '2017-08-29T18:58:43+00:00',
        'height': 2481.301,
        'x_velocity': 0.0,
        'y_velocity': 0.01,
        'z_velocity': 0.0}
    
    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 26)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()