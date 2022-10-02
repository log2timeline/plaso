# -*- coding: utf-8 -*-
"""This file contains the event data registry class."""


class EventDataRegistry(object):
  """Class that implements the event data registry."""

  _event_data_classes = {}

  @classmethod
  def DeregisterEventDataClass(cls, event_data_class):
    """Deregisters an event data class.

    The event data classes are identified based on their lower case data type.

    Args:
      event_data_class (type): event data class.

    Raises:
      KeyError: if event data class is not set for the corresponding data type.
    """
    data_type = event_data_class.DATA_TYPE.lower()
    if data_type not in cls._event_data_classes:
      raise KeyError('Event data class not set for data type: {0:s}.'.format(
          event_data_class.DATA_TYPE))

    del cls._event_data_classes[data_type]

  @classmethod
  def GetAttributeMappings(cls, data_type):
    """Retrieves the attribute mappings of a specific event data.

    Args:
      data_type (str): data type.

    Returns:
      dict[str, str]: attribute mappings or None if not available.
    """
    event_data_class = cls._event_data_classes.get(data_type.lower(), None)
    if event_data_class:
      return getattr(event_data_class, 'ATTRIBUTE_MAPPINGS', None)

    return None

  @classmethod
  def RegisterEventDataClass(cls, event_data_class):
    """Registers an event data class.

    The event data classes are identified based on their lower case data type.

    Args:
      event_data_class (type): event data class.

    Raises:
      KeyError: if event data class is already set for the corresponding data
          type.
    """
    data_type = event_data_class.DATA_TYPE.lower()
    if data_type in cls._event_data_classes:
      raise KeyError(
          'Event data class already set for data type: {0:s}.'.format(
              event_data_class.DATA_TYPE))

    cls._event_data_classes[data_type] = event_data_class

  @classmethod
  def RegisterEventDataClasses(cls, event_data_classes):
    """Registers event data classes.

    The event data classes are identified based on their lower case data type.

    Args:
      event_data_classes (list[type]): event data classes.

    Raises:
      KeyError: if event data class is already set for the corresponding data
          type.
    """
    for event_data_class in event_data_classes:
      cls.RegisterEventDataClass(event_data_class)
