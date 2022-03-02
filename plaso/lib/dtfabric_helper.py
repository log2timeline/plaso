# -*- coding: utf-8 -*-
"""The dtFabric helper mix-in."""

import os

from dtfabric import errors as dtfabric_errors
from dtfabric.runtime import data_maps as dtfabric_data_maps
from dtfabric.runtime import fabric as dtfabric_fabric

from plaso.lib import errors


class DtFabricHelper(object):
  """dtFabric format definition helper mix-in.

  dtFabric defines its data format structures in dtFabric definition file,
  for example "dtfabric.yaml":

  name: int32
  type: integer
  description: 32-bit signed integer type
  attributes:
    format: signed
    size: 4
    units: bytes
  ---
  name: point3d
  aliases: [POINT]
  type: structure
  description: Point in 3 dimensional space.
  attributes:
    byte_order: little-endian
  members:
  - name: x
    aliases: [XCOORD]
    data_type: int32
  - name: y
    data_type: int32
  - name: z
    data_type: int32

  The path to the definition file is defined in the class constant
  "_DEFINITION_FILE" and will be read on class instantiation.

  The definition files contains data type definitions such as "int32" and
  "point3d" in the previous example.

  A data type map can be used to create a Python object that represent the
  data type definition mapped to a byte stream, for example if we have the
  following byte stream: 01 00 00 00 02 00 00 00 03 00 00 00

  The corresponding "point3d" Python object would be: point3d(x=1, y=2, z=3)
  """

  # The dtFabric definition file, which must be overwritten by a subclass.
  _DEFINITION_FILE = None

  def __init__(self):
    """Initializes the dtFabric format definition helper mix-in."""
    super(DtFabricHelper, self).__init__()
    self._data_type_maps = {}
    self._fabric = self._ReadDefinitionFile(self._DEFINITION_FILE)

  def _FormatPackedIPv4Address(self, packed_ip_address):
    """Formats a packed IPv4 address as a human readable string.

    Args:
      packed_ip_address (list[int]): packed IPv4 address.

    Returns:
      str: human readable IPv4 address.
    """
    return '.'.join(['{0:d}'.format(octet) for octet in packed_ip_address[:4]])

  def _FormatPackedIPv6Address(self, packed_ip_address):
    """Formats a packed IPv6 address as a human readable string.

    Args:
      packed_ip_address (list[int]): packed IPv6 address.

    Returns:
      str: human readable IPv6 address.
    """
    # Note that socket.inet_ntop() is not supported on Windows.
    octet_pairs = zip(packed_ip_address[0::2], packed_ip_address[1::2])
    octet_pairs = [octet1 << 8 | octet2 for octet1, octet2 in octet_pairs]
    # TODO: omit ":0000" from the string.
    return ':'.join([
        '{0:04x}'.format(octet_pair) for octet_pair in octet_pairs])

  def _GetDataTypeMap(self, name):
    """Retrieves a data type map defined by the definition file.

    The data type maps are cached for reuse.

    Args:
      name (str): name of the data type as defined by the definition file.

    Returns:
      dtfabric.DataTypeMap: data type map which contains a data type definition,
          such as a structure, that can be mapped onto binary data.
    """
    data_type_map = self._data_type_maps.get(name, None)
    if not data_type_map:
      data_type_map = self._fabric.CreateDataTypeMap(name)
      self._data_type_maps[name] = data_type_map

    return data_type_map

  def _ReadData(self, file_object, file_offset, data_size):
    """Reads data.

    Args:
      file_object (dfvfs.FileIO): a file-like object to read.
      file_offset (int): offset of the data relative to the start of
          the file-like object.
      data_size (int): size of the data. The resulting data size much match
          the requested data size so that dtFabric can map the data type
          definitions onto the byte stream.

    Returns:
      bytes: byte stream containing the data.

    Raises:
      ParseError: if the data cannot be read.
      ValueError: if the file-like object is missing.
    """
    if not file_object:
      raise ValueError('Missing file-like object.')

    file_object.seek(file_offset, os.SEEK_SET)

    read_error = ''

    try:
      data = file_object.read(data_size)

      if len(data) != data_size:
        read_error = 'missing data'

    except IOError as exception:
      read_error = '{0!s}'.format(exception)

    if read_error:
      raise errors.ParseError(
          'Unable to read data at offset: 0x{0:08x} with error: {1:s}'.format(
              file_offset, read_error))

    return data

  def _ReadDefinitionFile(self, path):
    """Reads a dtFabric definition file.

    Args:
      path (str): path of the dtFabric definition file.

    Returns:
      dtfabric.DataTypeFabric: data type fabric which contains the data format
          data type maps of the data type definition, such as a structure, that
          can be mapped onto binary data or None if no path is provided.
    """
    if not path:
      return None

    with open(path, 'rb') as file_object:
      definition = file_object.read()

    return dtfabric_fabric.DataTypeFabric(yaml_definition=definition)

  def _ReadStructureFromByteStream(
      self, byte_stream, file_offset, data_type_map, context=None):
    """Reads a structure from a byte stream.

    Args:
      byte_stream (bytes): byte stream.
      file_offset (int): offset of the structure data relative to the start
          of the file-like object.
      data_type_map (dtfabric.DataTypeMap): data type map of the structure.
      context (Optional[dtfabric.DataTypeMapContext]): data type map context.
          The context is used within dtFabric to hold state about how to map
          the data type definition onto the byte stream. In this class it is
          used to determine the size of variable size data type definitions.

    Returns:
      object: structure values object.

    Raises:
      ParseError: if the structure cannot be read.
      ValueError: if file-like object or data type map is missing.
    """
    if not byte_stream:
      raise ValueError('Missing byte stream.')

    if not data_type_map:
      raise ValueError('Missing data type map.')

    try:
      return data_type_map.MapByteStream(byte_stream, context=context)
    except (dtfabric_errors.ByteStreamTooSmallError,
            dtfabric_errors.MappingError) as exception:
      raise errors.ParseError((
          'Unable to map {0:s} data at offset: 0x{1:08x} with error: '
          '{2!s}').format(data_type_map.name or '', file_offset, exception))

  def _ReadStructureFromFileObject(
      self, file_object, file_offset, data_type_map):
    """Reads a structure from a file-like object.

    If the data type map has a fixed size this method will read the predefined
    number of bytes from the file-like object. If the data type map has a
    variable size, depending on values in the byte stream, this method will
    continue to read from the file-like object until the data type map can be
    successfully mapped onto the byte stream or until an error occurs.

    Args:
      file_object (dfvfs.FileIO): a file-like object to parse.
      file_offset (int): offset of the structure data relative to the start
          of the file-like object.
      data_type_map (dtfabric.DataTypeMap): data type map of the structure.

    Returns:
      tuple[object, int]: structure values object and data size of
          the structure.

    Raises:
      ParseError: if the structure cannot be read.
      ValueError: if file-like object or data type map is missing.
    """
    context = None
    data = b''
    last_data_size = 0

    data_size = data_type_map.GetSizeHint()

    while data_size != last_data_size:
      read_offset = file_offset + last_data_size
      read_size = data_size - last_data_size
      data_segment = self._ReadData(file_object, read_offset, read_size)

      data = b''.join([data, data_segment])

      try:
        context = dtfabric_data_maps.DataTypeMapContext()
        structure_values_object = data_type_map.MapByteStream(
            data, context=context)
        return structure_values_object, data_size

      except dtfabric_errors.ByteStreamTooSmallError:
        pass

      except dtfabric_errors.MappingError as exception:
        raise errors.ParseError((
            'Unable to map {0:s} data at offset: 0x{1:08x} with error: '
            '{2!s}').format(data_type_map.name, file_offset, exception))

      last_data_size = data_size
      data_size = data_type_map.GetSizeHint(context=context)

    raise errors.ParseError(
        'Unable to read {0:s} at offset: 0x{1:08x}'.format(
            data_type_map.name, file_offset))
