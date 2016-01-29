# -*- coding: utf-8 -*-
"""This file contains the storage factory class."""

from plaso.lib import py2to3


class StorageFactory(object):
  """Class that implements the storage factory."""

  _storage_classes = {}

  @classmethod
  def DeregisterStorage(cls, storage_class):
    """Deregisters a storage class.

    The storage classes are identified based on their NAME attribute.

    Args:
      storage_class: the class object of the storage.

    Raises:
      KeyError: if storage class is not set for the corresponding data type.
    """
    storage_class_name = storage_class.NAME.lower()
    if storage_class_name not in cls._storage_classes:
      raise KeyError(
          u'Storage class not set for name: {0:s}.'.format(
              storage_class.NAME))

    del cls._storage_classes[storage_class_name]

  @classmethod
  def GetAllTypeIndicators(cls):
    """Get all registered type indicators."""
    return cls._storage_classes.keys()

  @classmethod
  def NewStorage(cls, type_indicator):
    """Creates a new storage instance for a specific type.

    Args:
      type_indicator: the type indocator of the storage.

    Returns:
      The corresponding storage (instance of StorageFile).

    Raises:
      KeyError: if the type indicator is not registered.
      ValueError: if the type indicator is not a string.
    """
    if not isinstance(type_indicator, py2to3.STRING_TYPES):
      raise ValueError(u'Type indicator is not a string.')

    type_indicator = type_indicator.lower()
    if type_indicator not in cls._storage_classes:
      raise KeyError(
          u'Storage implementation not registered for name: {0:s}.'.format(
              type_indicator))

    storage_class = cls._storage_classes[type_indicator]

    return storage_class()

  @classmethod
  def RegisterStorage(cls, storage_class):
    """Registers a storage class.

    The storage classes are identified based on their NAME attribute.

    Args:
      storage_class: the class object of the storage (instance of StorageFile).

    Raises:
      KeyError: if storage class is already set for the corresponding
                name attribute.
    """
    storage_name = storage_class.NAME.lower()
    if storage_name in cls._storage_classes:
      raise KeyError((
          u'Storage class already set for name: {0:s}.').format(
              storage_class.NAME))

    cls._storage_classes[storage_name] = storage_class

  @classmethod
  def RegisterStorages(cls, storage_classes):
    """Registers storage classes.

    The storage classes are identified based on their NAME attribute.

    Args:
      storage_classes: a list of class objects of the storages (instance of
                       StorageFile).

    Raises:
      KeyError: if storage class is already set for the corresponding name.
    """
    for storage_class in storage_classes:
      cls.RegisterStorage(storage_class)
