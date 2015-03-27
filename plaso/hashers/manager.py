# -*- coding: utf-8 -*-
"""This file contains a class for managing digest hashers for Plaso."""


class HashersManager(object):
  """Class that implements the hashers manager."""

  _hasher_classes = {}

  @classmethod
  def DeregisterHasher(cls, hasher_class):
    """Deregisters a hasher class.

    The hasher classes are identified based on their lower case name.

    Args:
      hasher_class: the class object of the hasher.

    Raises:
      KeyError: if hasher class is not set for the corresponding name.
    """
    hasher_name = hasher_class.NAME.lower()
    if hasher_name not in cls._hasher_classes:
      raise KeyError(
          u'hasher class not set for name: {0:s}.'.format(
              hasher_class.NAME))

    del cls._hasher_classes[hasher_name]

  @classmethod
  def GetHasherNamesFromString(cls, hasher_names_string):
    """Retrieves a list of a hasher names from a comma separated string.

    Takes a string of comma separated hasher names transforms it to a list of
    hasher names.

    Args:
      hasher_names_string: Comma separated string of names of
                           hashers to enable enable.

    Returns:
      A list of names of valid hashers from the string, or an empty list if
      no valid names are found.
    """
    hasher_names = []

    for hasher_name in hasher_names_string.split(u','):
      hasher_name = hasher_name.strip()
      if not hasher_name:
        continue

      hasher_name = hasher_name.lower()
      if hasher_name in cls._hasher_classes:
        hasher_names.append(hasher_name)

    return hasher_names

  @classmethod
  def GetHasherNames(cls):
    """Retrieves the names of all loaded hashers.

    Returns:
      A list of hasher names.
    """
    return cls._hasher_classes.keys()

  @classmethod
  def GetHasherObject(cls, hasher_name):
    """Retrieves an instance of a specific hasher.

    Args:
      hasher_name: The name of the hasher to retrieve.

    Returns:
      A hasher object (instance of BaseHasher).

    Raises:
      KeyError: if hasher class is not set for the corresponding name.
    """
    hasher_name = hasher_name.lower()
    if hasher_name not in cls._hasher_classes:
      raise KeyError(
          u'hasher class not set for name: {0:s}.'.format(hasher_name))

    hasher_class = cls._hasher_classes[hasher_name]
    return hasher_class()

  @classmethod
  def GetHasherObjects(cls, hasher_names):
    """Retrieves instances for all the specified hashers.

    Args:
      hasher_names: List of the names of the hashers to retrieve.

    Returns:
      A list of hasher objects (instances of BaseHasher).
    """
    hasher_objects = []
    for hasher_name, hasher_class in cls._hasher_classes.iteritems():
      if hasher_name in hasher_names:
        hasher_objects.append(hasher_class())

    return hasher_objects

  @classmethod
  def GetHashers(cls):
    """Retrieves the registered hashers.

    Yields:
      A tuple that contains the uniquely identifying name of the hasher
      and the hasher class (subclass of BaseHasher).
    """
    for hasher_name, hasher_class in cls._hasher_classes.iteritems():
      yield hasher_name, hasher_class

  @classmethod
  def RegisterHasher(cls, hasher_class):
    """Registers a hasher class.

    The hasher classes are identified based on their lower case name.

    Args:
      hasher_class: the class object of the hasher.

    Raises:
      KeyError: if hasher class is already set for the corresponding name.
    """
    hasher_name = hasher_class.NAME.lower()
    if hasher_name in cls._hasher_classes:
      raise KeyError((
          u'hasher class already set for name: {0:s}.').format(
              hasher_class.NAME))

    cls._hasher_classes[hasher_name] = hasher_class
