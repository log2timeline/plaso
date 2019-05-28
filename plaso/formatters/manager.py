# -*- coding: utf-8 -*-
"""This file contains the event formatters manager class."""

from __future__ import unicode_literals

from plaso.formatters import default
from plaso.formatters import logger
from plaso.lib import definitions
from plaso.formatters import yaml_formatters_file


class FormattersManager(object):
  """Class that implements the formatters manager."""

  _formatter_classes = {}
  _formatter_objects = {}
  _unformatted_attributes = {}

  # Work-around to prevent the tests re-reading the formatters file.
  _file_was_read = False

  @classmethod
  def DeregisterFormatter(cls, formatter_class):
    """Deregisters a formatter class.

    The formatter classes are identified based on their lower case data type.

    Args:
      formatter_class (type): class of the formatter.

    Raises:
      KeyError: if formatter class is not set for the corresponding data type.
    """
    formatter_data_type = formatter_class.DATA_TYPE.lower()
    if formatter_data_type not in cls._formatter_classes:
      raise KeyError('Formatter class not set for data type: {0:s}.'.format(
          formatter_class.DATA_TYPE))

    del cls._formatter_classes[formatter_data_type]

  @classmethod
  def GetFormatterObject(cls, data_type):
    """Retrieves the formatter object for a specific data type.

    Args:
      data_type (str): data type.

    Returns:
      EventFormatter: corresponding formatter or the default formatter if
          not available.
    """
    data_type = data_type.lower()
    if data_type not in cls._formatter_objects:
      formatter_object = None

      if data_type in cls._formatter_classes:
        formatter_class = cls._formatter_classes[data_type]
        # TODO: remove the need to instantiate the Formatter classes
        # and use class methods only.
        formatter_object = formatter_class()

      if not formatter_object:
        logger.warning('Using default formatter for data type: {0:s}'.format(
            data_type))
        formatter_object = default.DefaultFormatter()

      cls._formatter_objects[data_type] = formatter_object

    return cls._formatter_objects[data_type]

  @classmethod
  def GetMessageStrings(cls, formatter_mediator, event_data):
    """Retrieves the formatted message strings for a specific event.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event_data (EventData): event data.

    Returns:
      list[str, str]: long and short version of the message string.
    """
    formatter_object = cls.GetFormatterObject(event_data.data_type)
    return formatter_object.GetMessages(formatter_mediator, event_data)

  @classmethod
  def GetSourceStrings(cls, event, event_data):
    """Retrieves the formatted source strings for a specific event.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.

    Returns:
      list[str, str]: short and long version of the source of the event.
    """
    # TODO: change this to return the long variant first so it is consistent
    # with GetMessageStrings.
    formatter_object = cls.GetFormatterObject(event_data.data_type)
    return formatter_object.GetSources(event, event_data)

  @classmethod
  def GetUnformattedAttributes(cls, event_data):
    """Retrieves names of the event data attributes that are not formatted.

    Args:
      event_data (EventData): event data.

    Returns:
      list[str]: names of the event data attributes that are not formatted.
    """
    unformatted_attributes = cls._unformatted_attributes.get(
        event_data.data_type, None)
    if not unformatted_attributes:
      formatter_object = cls.GetFormatterObject(event_data.data_type)

      event_data_attribute_names = set(event_data.GetAttributeNames())

      formatter_attribute_names = (
          formatter_object.GetFormatStringAttributeNames())
      formatter_attribute_names.update(definitions.RESERVED_VARIABLE_NAMES)

      unformatted_attributes = sorted(event_data_attribute_names.difference(
          formatter_attribute_names))
      cls._unformatted_attributes[event_data.data_type] = unformatted_attributes

    return unformatted_attributes

  @classmethod
  def ReadFormattersFromFile(cls, path):
    """Reads formatters from a file.

    Args:
      path (str): path of file that contains the formatters configuration.

    Raises:
      KeyError: if formatter class is already set for the corresponding
          data type.
    """
    if not cls._file_was_read:
      formatters_file = yaml_formatters_file.YAMLFormattersFile()
      for formatter in formatters_file.ReadFromFile(path):
        # TODO: refactor RegisterFormatter to only use formatter objects.
        cls.RegisterFormatter(formatter)

        data_type = formatter.DATA_TYPE.lower()
        cls._formatter_objects[data_type] = formatter

      cls._file_was_read = True

  @classmethod
  def RegisterFormatter(cls, formatter_class):
    """Registers a formatter class.

    The formatter classes are identified based on their lower case data type.

    Args:
      formatter_class (type): class of the formatter.

    Raises:
      KeyError: if formatter class is already set for the corresponding
          data type.
    """
    formatter_data_type = formatter_class.DATA_TYPE.lower()
    if formatter_data_type in cls._formatter_classes:
      raise KeyError('Formatter class already set for data type: {0:s}.'.format(
          formatter_class.DATA_TYPE))

    cls._formatter_classes[formatter_data_type] = formatter_class

  @classmethod
  def RegisterFormatters(cls, formatter_classes):
    """Registers formatter classes.

    The formatter classes are identified based on their lower case data type.

    Args:
      formatter_classes (list[type]): classes of the formatters.

    Raises:
      KeyError: if formatter class is already set for the corresponding
          data type.
    """
    for formatter_class in formatter_classes:
      cls.RegisterFormatter(formatter_class)
