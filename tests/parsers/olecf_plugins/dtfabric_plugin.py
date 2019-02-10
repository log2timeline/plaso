# -*- coding: utf-8 -*-
"""Tests for shared functionality for dtFabric-based data format plugins."""

from __future__ import unicode_literals

import io
import unittest

from dtfabric import errors as dtfabric_errors
from dtfabric.runtime import data_maps as dtfabric_data_maps
from dtfabric.runtime import fabric as dtfabric_fabric

from plaso.lib import errors
from plaso.parsers.olecf_plugins import dtfabric_plugin

from tests.parsers.olecf_plugins import test_lib


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


class DtFabricBaseOLECFPluginTest(test_lib.OLECFPluginTestCase):
  """Shared functionality for dtFabric-based data format plugins tests."""

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

  _POINT3D = _DATA_TYPE_FABRIC.CreateDataTypeMap('point3d')

  _POINT3D_SIZE = _POINT3D.GetByteSize()

  _SHAPE3D = _DATA_TYPE_FABRIC.CreateDataTypeMap('shape3d')

  # TODO: add tests for _GetDataTypeMap

  def testReadData(self):
    """Tests the _ReadData function."""
    parser = dtfabric_plugin.DtFabricBaseOLECFPlugin()

    file_object = io.BytesIO(
        b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00')

    parser._ReadData(file_object, 0, self._POINT3D_SIZE)

    # Test with missing file-like object.
    with self.assertRaises(ValueError):
      parser._ReadData(None, 0, self._POINT3D_SIZE)

    # Test with file-like object with insufficient data.
    file_object = io.BytesIO(
        b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00')

    with self.assertRaises(errors.ParseError):
      parser._ReadData(file_object, 0, self._POINT3D_SIZE)

    # Test with file-like object that raises an IOError.
    file_object = ErrorBytesIO(
        b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00')

    with self.assertRaises(errors.ParseError):
      parser._ReadData(file_object, 0, self._POINT3D_SIZE)

  # TODO: add tests for _ReadDefinitionFile

  def testReadStructureFromByteStream(self):
    """Tests the _ReadStructureFromByteStream function."""
    parser = dtfabric_plugin.DtFabricBaseOLECFPlugin()

    parser._ReadStructureFromByteStream(
        b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00', 0,
        self._POINT3D)

    # Test with missing byte stream.
    with self.assertRaises(ValueError):
      parser._ReadStructureFromByteStream(None, 0, self._POINT3D)

    # Test with missing data map type.
    with self.assertRaises(ValueError):
      parser._ReadStructureFromByteStream(
          b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00', 0, None)

    # Test with data type map that raises an dtfabric.MappingError.
    data_type_map = ErrorDataTypeMap(None)

    with self.assertRaises(errors.ParseError):
      parser._ReadStructureFromByteStream(
          b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00', 0,
          data_type_map)

  def testReadStructureFromFileObject(self):
    """Tests the _ReadStructureFromFileObject function."""
    parser = dtfabric_plugin.DtFabricBaseOLECFPlugin()

    file_object = io.BytesIO(
        b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00')

    parser._ReadStructureFromFileObject(file_object, 0, self._POINT3D)

    file_object = io.BytesIO(
        b'\x03\x00\x00\x00'
        b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00'
        b'\x04\x00\x00\x00\x05\x00\x00\x00\x06\x00\x00\x00'
        b'\x06\x00\x00\x00\x07\x00\x00\x00\x08\x00\x00\x00')

    parser._ReadStructureFromFileObject(file_object, 0, self._SHAPE3D)


if __name__ == '__main__':
  unittest.main()
