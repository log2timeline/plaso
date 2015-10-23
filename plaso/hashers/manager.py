# -*- coding: utf-8 -*-
"""This file contains a class for managing digest hashers for Plaso."""

import os


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
      hasher_names_string: comma separated string of names of
                           hashers to enable, the string 'all' to enable all
                           hashers or 'none' to disable all hashers.

    Returns:
      A list of names of valid hashers from the string, or an empty list if
      no valid names are found.
    """
    hasher_names = []

    if not hasher_names_string or hasher_names_string.strip() == u'none':
      return hasher_names

    if hasher_names_string.strip() == u'all':
      return cls.GetHasherNames()

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
  def GetHashersInformation(cls):
    """Retrieves the hashers information.

    Returns:
      A list of tuples of hasher names and descriptions.
    """
    hashers_information = []
    for _, hasher_class in cls.GetHashers():
      description = getattr(hasher_class, u'DESCRIPTION', u'')
      hashers_information.append((hasher_class.NAME, description))

    return hashers_information

  @classmethod
  def GetHasherObject(cls, hasher_name):
    """Retrieves an instance of a specific hasher.

    Args:
      hasher_name: the name of the hasher to retrieve.

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
      hasher_names: list of the names of the hashers to retrieve.

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
  def HashFileObject(cls, hasher_names_string, file_object, buffer_size=4096):
    """Hashes the contents of a file-like object.

    Args:
      hasher_names_string: comma separated string of names of
                           hashers to enable enable, or the string 'all', to
                           enable all hashers.
      file_object: the file-like object to be hashed.
      buffer_size: optional read buffer size.

    Returns:
      A dictionary of digest hashes, where the key contains digest hash name
      and value contains the digest hash calculated from the file contents.
    """
    hasher_objects = cls.GetHasherObjects(hasher_names_string)
    if not hasher_objects:
      return {}

    file_object.seek(0, os.SEEK_SET)

    # We only do one read, then pass it to each of the hashers in turn.
    data = file_object.read(buffer_size)
    while data:
      for hasher_object in hasher_objects:
        hasher_object.Update(data)
      data = file_object.read(buffer_size)

    # Get the digest hash value of every active hasher.
    digest_hashes = {}
    for hasher_object in hasher_objects:
      digest_hashes[hasher_object.NAME] = hasher_object.GetStringDigest()

    return digest_hashes

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
