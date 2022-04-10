# -*- coding: utf-8 -*-
"""Tests for the dtFabric format definition helper mix-in."""

import io
import unittest

from dtfabric import errors as dtfabric_errors
from dtfabric.runtime import data_maps as dtfabric_data_maps
from dtfabric.runtime import fabric as dtfabric_fabric

from plaso.lib import dtfabric_helper
from plaso.lib import errors

from tests import test_lib


class ErrorBytesIO(io.BytesIO):
  """Bytes IO that errors."""

  # The following methods are part of the file-like object interface.
  # pylint: disable=invalid-name

  def read(self, size=None):  # pylint: disable=unused-argument
    """Reads bytes.

    Args:
      size (Optional[int]): number of bytes to read, where None represents
          all remaining bytes.

    Raises:
      IOError: for testing.
      OSError: for testing.
    """
    raise IOError('Unable to read for testing purposes.')


class ErrorDataTypeMap(dtfabric_data_maps.DataTypeMap):
  """Data type map that errors."""

  def FoldByteStream(self, mapped_value, **unused_kwargs):
    """Folds the data type into a byte stream.

    Args:
      mapped_value (object): mapped value.

    Raises:
      FoldingError: for testing.
    """
    raise dtfabric_errors.FoldingError(
        'Unable to fold to byte stream for testing purposes.')

  def MapByteStream(self, byte_stream, **unused_kwargs):
    """Maps the data type on a byte stream.

    Args:
      byte_stream (bytes): byte stream.

    Raises:
      dtfabric.MappingError: for testing.
    """
    raise dtfabric_errors.MappingError(
        'Unable to map byte stream for testing purposes.')


class DtFabricHelperTest(test_lib.BaseTestCase):
  """dtFabric format definition helper mix-in tests."""

  # pylint: disable=protected-access

  _DATA_TYPE_FABRIC_DEFINITION = b"""\
name: uint32
type: integer
attributes:
  format: unsigned
  size: 4
  units: bytes
---
name: point3d
type: structure
attributes:
  byte_order: little-endian
members:
- name: x
  data_type: uint32
- name: y
  data_type: uint32
- name: z
  data_type: uint32
---
name: shape3d
type: structure
attributes:
  byte_order: little-endian
members:
- name: number_of_points
  data_type: uint32
- name: points
  type: sequence
  element_data_type: point3d
  number_of_elements: shape3d.number_of_points
"""

  _DATA_TYPE_FABRIC = dtfabric_fabric.DataTypeFabric(
      yaml_definition=_DATA_TYPE_FABRIC_DEFINITION)

  def testFormatPackedIPv4Address(self):
    """Tests the _FormatPackedIPv4Address function."""
    test_helper = dtfabric_helper.DtFabricHelper()

    ip_address = test_helper._FormatPackedIPv4Address([0xc0, 0xa8, 0xcc, 0x62])
    self.assertEqual(ip_address, '192.168.204.98')

  def testFormatPackedIPv6Address(self):
    """Tests the _FormatPackedIPv6Address function."""
    test_helper = dtfabric_helper.DtFabricHelper()

    ip_address = test_helper._FormatPackedIPv6Address([
        0x20, 0x01, 0x0d, 0xb8, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0x00,
        0x00, 0x42, 0x83, 0x29])
    self.assertEqual(ip_address, '2001:0db8:0000:0000:0000:ff00:0042:8329')

  # TODO: add tests for _GetDataTypeMap

  def testReadData(self):
    """Tests the _ReadData function."""
    test_helper = dtfabric_helper.DtFabricHelper()

    file_object = io.BytesIO(
        b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00')

    test_helper._ReadData(file_object, 0, 12)

    # Test with missing file-like object.
    with self.assertRaises(ValueError):
      test_helper._ReadData(None, 0, 12)

    # Test with file-like object with insufficient data.
    file_object = io.BytesIO(
        b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00')

    with self.assertRaises(errors.ParseError):
      test_helper._ReadData(file_object, 0, 12)

    # Test with file-like object that raises an IOError.
    file_object = ErrorBytesIO(
        b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00')

    with self.assertRaises(errors.ParseError):
      test_helper._ReadData(file_object, 0, 12)

  # TODO: add tests for _ReadDefinitionFile

  def testReadStructureFromByteStream(self):
    """Tests the _ReadStructureFromByteStream function."""
    test_helper = dtfabric_helper.DtFabricHelper()

    data_type_map = self._DATA_TYPE_FABRIC.CreateDataTypeMap('point3d')

    test_helper._ReadStructureFromByteStream(
        b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00', 0,
        data_type_map)

    # Test with missing byte stream.
    with self.assertRaises(ValueError):
      test_helper._ReadStructureFromByteStream(None, 0, data_type_map)

    # Test with missing data map type.
    with self.assertRaises(ValueError):
      test_helper._ReadStructureFromByteStream(
          b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00', 0, None)

    # Test with data type map that raises an dtfabric.MappingError.
    data_type_map = ErrorDataTypeMap(None)

    with self.assertRaises(errors.ParseError):
      test_helper._ReadStructureFromByteStream(
          b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00', 0,
          data_type_map)

  def testReadStructureFromFileObject(self):
    """Tests the _ReadStructureFromFileObject function."""
    test_helper = dtfabric_helper.DtFabricHelper()

    file_object = io.BytesIO(
        b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00')

    data_type_map = self._DATA_TYPE_FABRIC.CreateDataTypeMap('point3d')
    test_helper._ReadStructureFromFileObject(file_object, 0, data_type_map)

    file_object = io.BytesIO(
        b'\x03\x00\x00\x00'
        b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00'
        b'\x04\x00\x00\x00\x05\x00\x00\x00\x06\x00\x00\x00'
        b'\x06\x00\x00\x00\x07\x00\x00\x00\x08\x00\x00\x00')

    data_type_map = self._DATA_TYPE_FABRIC.CreateDataTypeMap('shape3d')
    test_helper._ReadStructureFromFileObject(file_object, 0, data_type_map)


if __name__ == '__main__':
  unittest.main()
