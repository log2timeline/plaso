# -*- coding: utf-8 -*-
"""Shared functionality for dtFabric-based data format parsers."""

from __future__ import unicode_literals

import abc
import os

from dtfabric import errors as dtfabric_errors
from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.lib import errors
from plaso.parsers import interface


class DataFormatParser(interface.FileObjectParser):
  """Shared functionality for dtFabric-based data format parsers."""

  def _ReadData(self, file_object, file_offset, data_size, description):
    """Reads data.

    Args:
      file_object (file): a file-like object.
      file_offset (int): offset of the data relative from the start of
          the file-like object.
      data_size (int): size of the data.
      description (str): description of the data.

    Returns:
      bytes: byte stream containing the data.

    Raises:
      ParseError: if the structure cannot be read.
      ValueError: if file-like object or data type map are invalid.
    """
    if not file_object:
      raise ValueError('Invalid file-like object.')

    file_object.seek(file_offset, os.SEEK_SET)

    read_error = ''

    try:
      data = file_object.read(data_size)

      if len(data) != data_size:
        read_error = 'missing data'

    except IOError as exception:
      read_error = '{0!s}'.format(exception)

    if read_error:
      raise errors.ParseError((
          'Unable to read {0:s} data at offset: 0x{1:08x} with error: '
          '{2:s}').format(description, file_offset, read_error))

    return data

  def _ReadStructure(
      self, file_object, file_offset, data_size, data_type_map, description):
    """Reads a structure.

    Args:
      file_object (file): a file-like object.
      file_offset (int): offset of the data relative from the start of
          the file-like object.
      data_size (int): data size of the structure.
      data_type_map (dtfabric.DataTypeMap): data type map of the structure.
      description (str): description of the structure.

    Returns:
      object: structure values object.

    Raises:
      ParseError: if the structure cannot be read.
      ValueError: if file-like object or data type map are invalid.
    """
    data = self._ReadData(file_object, file_offset, data_size, description)

    return self._ReadStructureFromByteStream(
        data, file_offset, data_type_map, description)

  def _ReadStructureWithSizeHint(
      self, file_object, file_offset, data_type_map, description):
    """Reads a structure using a size hint.

    Args:
      file_object (file): a file-like object.
      file_offset (int): offset of the data relative from the start of
          the file-like object.
      data_type_map (dtfabric.DataTypeMap): data type map of the structure.
      description (str): description of the structure.

    Returns:
      tuple[object, int]: structure values object and data size of
          the structure.

    Raises:
      ParseError: if the structure cannot be read.
      ValueError: if file-like object or data type map are invalid.
    """
    context = None
    last_size_hint = 0
    size_hint = data_type_map.GetSizeHint()

    while size_hint != last_size_hint:
      data = self._ReadData(file_object, file_offset, size_hint, description)

      try:
        context = dtfabric_data_maps.DataTypeMapContext()
        structure_values_object = self._ReadStructureFromByteStream(
            data, file_offset, data_type_map, description, context=context)
        return structure_values_object, size_hint

      except dtfabric_errors.ByteStreamTooSmallError:
        pass

      last_size_hint = size_hint
      size_hint = data_type_map.GetSizeHint(context=context)

    raise errors.ParseError('Unable to read {0:s}'.format(description))

  def _ReadStructureFromByteStream(
      self, byte_stream, file_offset, data_type_map, description, context=None):
    """Reads a structure from a byte stream.

    Args:
      byte_stream (bytes): byte stream.
      file_offset (int): offset of the data relative from the start of
          the file-like object.
      data_type_map (dtfabric.DataTypeMap): data type map of the structure.
      description (str): description of the structure.
      context (Optional[dtfabric.DataTypeMapContext]): data type map context.

    Returns:
      object: structure values object.

    Raises:
      ParseError: if the structure cannot be read.
      ValueError: if file-like object or data type map are invalid.
    """
    if not byte_stream:
      raise ValueError('Invalid byte stream.')

    if not data_type_map:
      raise ValueError('Invalid data type map.')

    try:
      return data_type_map.MapByteStream(byte_stream, context=context)
    except dtfabric_errors.MappingError as exception:
      raise errors.ParseError((
          'Unable to map {0:s} data at offset: 0x{1:08x} with error: '
          '{2!s}').format(description, file_offset, exception))

  @abc.abstractmethod
  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a file-like object.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
      file_object (dvfvs.FileIO): a file-like object to parse.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
