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
      hasher_class (type): class object of the hasher.

    Raises:
      KeyError: if hasher class is not set for the corresponding name.
    """
    hasher_name = hasher_class.NAME.lower()
    if hasher_name not in cls._hasher_classes:
      raise KeyError(
          'hasher class not set for name: {0:s}.'.format(
              hasher_class.NAME))

    del cls._hasher_classes[hasher_name]

  @classmethod
  def GetHasherNamesFromString(cls, hasher_names_string):
    """Retrieves a list of a hasher names from a comma separated string.

    Takes a string of comma separated hasher names transforms it to a list of
    hasher names.

    Args:
      hasher_names_string (str): comma separated names of hashers to enable,
          the string 'all' to enable all hashers or 'none' to disable all
          hashers.

    Returns:
      list[str]: names of valid hashers from the string, or an empty list if no
          valid names are found.
    """
    hasher_names = []

    if not hasher_names_string or hasher_names_string.strip() == 'none':
      return hasher_names

    if hasher_names_string.strip() == 'all':
      return cls.GetHasherNames()

    for hasher_name in hasher_names_string.split(','):
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
      list[str]: hasher names.
    """
    return cls._hasher_classes.keys()

  @classmethod
  def GetHashersInformation(cls):
    """Retrieves the hashers information.

    Returns:
      list[tuple]: containing:

          str: hasher name.
          str: hasher description.
    """
    hashers_information = []
    for _, hasher_class in cls.GetHasherClasses():
      description = getattr(hasher_class, 'DESCRIPTION', '')
      hashers_information.append((hasher_class.NAME, description))

    return hashers_information

  @classmethod
  def GetHasher(cls, hasher_name):
    """Retrieves an instance of a specific hasher.

    Args:
      hasher_name (str): the name of the hasher to retrieve.

    Returns:
      BaseHasher: hasher.

    Raises:
      KeyError: if hasher class is not set for the corresponding name.
    """
    hasher_name = hasher_name.lower()
    if hasher_name not in cls._hasher_classes:
      raise KeyError(
          'hasher class not set for name: {0:s}.'.format(hasher_name))

    hasher_class = cls._hasher_classes[hasher_name]
    return hasher_class()

  @classmethod
  def GetHashers(cls, hasher_names):
    """Retrieves instances for all the specified hashers.

    Args:
      hasher_names (list[str]): names of the hashers to retrieve.

    Returns:
      list[BaseHasher]: hashers.
    """
    hashers = []
    for hasher_name, hasher_class in cls._hasher_classes.items():
      if hasher_name in hasher_names:
        hashers.append(hasher_class())

    return hashers

  @classmethod
  def GetHasherClasses(cls, hasher_names=None):
    """Retrieves the registered hashers.

    Args:
      hasher_names (list[str]): names of the hashers to retrieve.

    Yields:
        tuple: containing:

         str: parser name
         type: next hasher class.
    """
    for hasher_name, hasher_class in cls._hasher_classes.items():
      if not hasher_names or hasher_name in hasher_names:
        yield hasher_name, hasher_class

  @classmethod
  def RegisterHasher(cls, hasher_class):
    """Registers a hasher class.

    The hasher classes are identified based on their lower case name.

    Args:
      hasher_class (type): class object of the hasher.

    Raises:
      KeyError: if hasher class is already set for the corresponding name.
    """
    hasher_name = hasher_class.NAME.lower()
    if hasher_name in cls._hasher_classes:
      raise KeyError((
          'hasher class already set for name: {0:s}.').format(
              hasher_class.NAME))

    cls._hasher_classes[hasher_name] = hasher_class
