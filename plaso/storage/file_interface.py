# -*- coding: utf-8 -*-
"""Storage interface classes for file-based stores."""

import collections

from plaso.lib import definitions
from plaso.serializer import json_serializer
from plaso.storage import interface


class BaseStorageFile(interface.BaseStore):
  """Interface for file-based stores."""

  # pylint: disable=abstract-method

  def __init__(self, storage_type=definitions.STORAGE_TYPE_SESSION):
    """Initializes a file-based store.

    Args:
      storage_type (Optional[str]): storage type.
    """
    super(BaseStorageFile, self).__init__(storage_type=storage_type)
    self._attribute_container_sequence_numbers = collections.Counter()
    self._is_open = False
    self._read_only = True
    self._serializer = json_serializer.JSONAttributeContainerSerializer

  def _GetAttributeContainerNextSequenceNumber(self, container_type):
    """Retrieves the next sequence number of an attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: next sequence number.
    """
    self._attribute_container_sequence_numbers[container_type] += 1
    return self._attribute_container_sequence_numbers[container_type]

  def _RaiseIfNotReadable(self):
    """Raises if the storage file is not readable.

     Raises:
      IOError: when the storage file is closed.
      OSError: when the storage file is closed.
    """
    if not self._is_open:
      raise IOError('Unable to read from closed storage file.')

  def _RaiseIfNotWritable(self):
    """Raises if the storage file is not writable.

    Raises:
      IOError: when the storage file is closed or read-only.
      OSError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError('Unable to write to closed storage file.')

    if self._read_only:
      raise IOError('Unable to write to read-only storage file.')

  def _SerializeAttributeContainer(self, attribute_container):
    """Serializes an attribute container.

    Args:
      attribute_container (AttributeContainer): attribute container.

    Returns:
      bytes: serialized attribute container.

    Raises:
      IOError: if the attribute container cannot be serialized.
      OSError: if the attribute container cannot be serialized.
    """
    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(
          attribute_container.CONTAINER_TYPE)

    try:
      attribute_container_data = self._serializer.WriteSerialized(
          attribute_container)
      if not attribute_container_data:
        raise IOError(
            'Unable to serialize attribute container: {0:s}.'.format(
                attribute_container.CONTAINER_TYPE))

      attribute_container_data = attribute_container_data.encode('utf-8')

    finally:
      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(
            attribute_container.CONTAINER_TYPE)

    return attribute_container_data

  def _SetAttributeContainerNextSequenceNumber(
      self, container_type, next_sequence_number):
    """Sets the next sequence number of an attribute container.

    Args:
      container_type (str): attribute container type.
      next_sequence_number (int): next sequence number.
    """
    self._attribute_container_sequence_numbers[
        container_type] = next_sequence_number
