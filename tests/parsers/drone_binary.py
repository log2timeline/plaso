"""Tests for the drone binary flight log parser."""
import unittest

from plaso.parsers import drone_binary
from tests.parsers import test_lib


class DroneBinaryParserTest(test_lib.ParserTestCase):
  """Tests for the DroneBinaryParser for drone flight logs."""

  def testParseFile(self):
    """Tests parsing a drone binary log file with one OSD and one CUSTOM record."""
    parser = drone_binary.DroneBinaryParser()
    storage_writer = self._ParseFile(['drone_test.txt'], parser)

    # Pastikan jumlah event data yang dihasilkan adalah 1.
    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data,  3147)

    # Pastikan tidak ada peringatan parsing (extraction/recovery warnings).
    number_of_extraction_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_extraction_warnings, 0)
    number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_recovery_warnings, 0)

    # Ambil event data pertama (satu-satunya).
    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)

    # Tentukan nilai-nilai yang diharapkan dari event data.
    expected_event_values = {
        'data_type': 'drone:flight:event',
        'longitude': -106.21639931363029,
        'latitude': 39.9612000043031,
        'height': 0,
        'distance': 1.2273155450820923,
        'speed': 0.0,
        'timestamp': '2017-08-29T18:05:27.929+00:00'
    }

    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
