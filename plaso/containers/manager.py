# -*- coding: utf-8 -*-
"""This file contains the attribute container manager class."""

from __future__ import unicode_literals


class AttributeContainersManager(object):
  """Class that implements the attribute container manager."""

  _attribute_container_classes = {}

  @classmethod
  def DeregisterAttributeContainer(cls, attribute_container_class):
    """Deregisters an attribute container class.

    The attribute container classes are identified based on their lower case
    container type.

    Args:
      attribute_container_class (type): attribute container class.

    Raises:
      KeyError: if attribute container class is not set for
                the corresponding container type.
    """
    container_type = attribute_container_class.CONTAINER_TYPE.lower()
    if container_type not in cls._attribute_container_classes:
      raise KeyError(
          'Attribute container class not set for container type: '
          '{0:s}.'.format(attribute_container_class.CONTAINER_TYPE))

    del cls._attribute_container_classes[container_type]

  @classmethod
  def GetAttributeContainer(cls, container_type):
    """Retrieves the attribute container for a specific container type.

    Args:
      container_type (str): container type.

    Returns:
      AttributeContainer: attribute container.
    """
    return cls._attribute_container_classes.get(container_type, None)

  @classmethod
  def RegisterAttributeContainer(cls, attribute_container_class):
    """Registers a attribute container class.

    The attribute container classes are identified based on their lower case
    container type.

    Args:
      attribute_container_class (type): attribute container class.

    Raises:
      KeyError: if attribute container class is already set for
                the corresponding container type.
    """
    container_type = attribute_container_class.CONTAINER_TYPE.lower()
    if container_type in cls._attribute_container_classes:
      raise KeyError((
          'Attribute container class already set for container type: '
          '{0:s}.').format(attribute_container_class.CONTAINER_TYPE))

    cls._attribute_container_classes[container_type] = attribute_container_class

  @classmethod
  def RegisterAttributeContainers(cls, attribute_container_classes):
    """Registers attribute container classes.

    The attribute container classes are identified based on their lower case
    container type.

    Args:
      attribute_container_classes (list[type]): attribute container classes.

    Raises:
      KeyError: if attribute container class is already set for
                the corresponding container type.
    """
    for attribute_container_class in attribute_container_classes:
      cls.RegisterAttributeContainer(attribute_container_class)
