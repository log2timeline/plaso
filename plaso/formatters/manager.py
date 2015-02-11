# -*- coding: utf-8 -*-
"""This file contains the event formatters manager class."""

import logging

from plaso.formatters import interface
from plaso.lib import utils


class DefaultFormatter(interface.EventFormatter):
  """Default formatter for events that do not have any defined formatter."""

  DATA_TYPE = u'event'
  FORMAT_STRING = u'<WARNING DEFAULT FORMATTER> Attributes: {attribute_driven}'
  FORMAT_STRING_SHORT = u'<DEFAULT> {attribute_driven}'

  def GetMessages(self, event_object):
    """Return a list of messages extracted from an event object."""
    text_pieces = []

    for key, value in event_object.GetValues().items():
      if key in utils.RESERVED_VARIABLES:
        continue
      text_pieces.append(u'{0:s}: {1!s}'.format(key, value))

    event_object.attribute_driven = u' '.join(text_pieces)
    # Due to the way the default formatter behaves it requires the data_type
    # to be set as 'event', otherwise it will complain and deny processing
    # the event.
    # TODO: Change this behavior and allow the default formatter to accept
    # arbitrary data types (as it should).
    old_data_type = getattr(event_object, 'data_type', None)
    event_object.data_type = self.DATA_TYPE
    msg, msg_short = super(DefaultFormatter, self).GetMessages(event_object)
    event_object.data_type = old_data_type
    return msg, msg_short


class FormattersManager(object):
  """Class that implements the formatters manager."""

  _formatter_classes = {}
  _formatter_objects = {}

  @classmethod
  def DeregisterFormatter(cls, formatter_class):
    """Deregisters a formatter class.

    The formatter classes are identified based on their lower case data type.

    Args:
      formatter_class: the class object of the formatter.

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
      data_type: The data type.

    Returns:
      The corresponding formatter (instance of EventFormatter) or
      the default formatter (instance of DefaultFormatter) if not available.
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
        formatter_object = DefaultFormatter()

      cls._formatter_objects[data_type] = formatter_object

    return cls._formatter_objects[data_type]

  @classmethod
  def GetMessageStrings(cls, event_object):
    """Retrieves the formatted message strings for a specific event object.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A list that contains both the longer and shorter version of the message
      string.
    """
    formatter_object = cls.GetFormatterObject(event_object.data_type)
    return formatter_object.GetMessages(event_object)

  @classmethod
  def GetSourceStrings(cls, event_object):
    """Retrieves the formatted source strings for a specific event object.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A list that contains the source_short and source_long version of the
      event.
    """
    # TODO: change this to return the long variant first so it is consistent
    # with GetMessageStrings.
    formatter_object = cls.GetFormatterObject(event_object.data_type)
    return formatter_object.GetSources(event_object)

  @classmethod
  def RegisterFormatter(cls, formatter_class):
    """Registers a formatter class.

    The formatter classes are identified based on their lower case data type.

    Args:
      formatter_class: the class object of the formatter.

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

    The formatter classes are identified based on their lower case name.

    Args:
      formatter_classes: a list of class objects of the formatters.

    Raises:
      KeyError: if formatter class is already set for the corresponding name.
    """
    for formatter_class in formatter_classes:
      cls.RegisterFormatter(formatter_class)
