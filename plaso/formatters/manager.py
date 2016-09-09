# -*- coding: utf-8 -*-
"""This file contains the event formatters manager class."""

import logging

from plaso.formatters import default


class FormattersManager(object):
  """Class that implements the formatters manager."""

  _formatter_classes = {}
  _formatter_objects = {}

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
      raise KeyError(
          u'Formatter class not set for data type: {0:s}.'.format(
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
        logging.warning(
            u'Using default formatter for data type: {0:s}'.format(data_type))
        formatter_object = default.DefaultFormatter()

      cls._formatter_objects[data_type] = formatter_object

    return cls._formatter_objects[data_type]

  @classmethod
  def GetMessageStrings(cls, formatter_mediator, event):
    """Retrieves the formatted message strings for a specific event object.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event (EventObject): event.

    Returns:
      list[str, str]: long and short version of the message string.
    """
    formatter_object = cls.GetFormatterObject(event.data_type)
    return formatter_object.GetMessages(formatter_mediator, event)

  @classmethod
  def GetSourceStrings(cls, event):
    """Retrieves the formatted source strings for a specific event object.

    Args:
      event (EventObject): event.

    Returns:
      list[str, str]: short and long version of the source of the event.
    """
    # TODO: change this to return the long variant first so it is consistent
    # with GetMessageStrings.
    formatter_object = cls.GetFormatterObject(event.data_type)
    return formatter_object.GetSources(event)

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
      raise KeyError((
          u'Formatter class already set for data type: {0:s}.').format(
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
