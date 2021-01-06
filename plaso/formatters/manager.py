# -*- coding: utf-8 -*-
"""Manages custom event formatter helpers."""


class FormattersManager(object):
  """Custom event formatter helpers manager."""

  _custom_formatter_helpers = {}

  @classmethod
  def GetEventFormatterHelper(cls, identifier):
    """Retrieves a custom event formatter helper.

    Args:
      identifier (str): identifier.

    Returns:
      CustomEventFormatterHelper: custom event formatter or None if not
          available.
    """
    identifier = identifier.lower()
    return cls._custom_formatter_helpers.get(identifier)

  @classmethod
  def RegisterEventFormatterHelper(cls, formatter_helper_class):
    """Registers a custom event formatter helper.

    The custom event formatter helpers are identified based on their lower
    case identifier.

    Args:
      formatter_helper_class (type): class of the custom event formatter helper.

    Raises:
      KeyError: if a custom formatter helper is already set for the
          corresponding identifier.
    """
    identifier = formatter_helper_class.IDENTIFIER.lower()
    if identifier in cls._custom_formatter_helpers:
      raise KeyError((
          'Custom event formatter helper already set for identifier: '
          '{0:s}.').format(formatter_helper_class.IDENTIFIER))

    cls._custom_formatter_helpers[identifier] = formatter_helper_class()

  @classmethod
  def RegisterEventFormatterHelpers(cls, formatter_helper_classes):
    """Registers custom event formatter helpers.

    The formatter classes are identified based on their lower case data type.

    Args:
      formatter_helper_classes (list[type]): classes of the custom event
          formatter helpers.

    Raises:
      KeyError: if a custom formatter helper is already set for the
          corresponding data type.
    """
    for formatter_helper_class in formatter_helper_classes:
      cls.RegisterEventFormatterHelper(formatter_helper_class)
