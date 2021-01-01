# -*- coding: utf-8 -*-
"""This file contains the event formatters manager class."""

import glob
import os

from plaso.formatters import default
from plaso.formatters import logger
from plaso.formatters import yaml_formatters_file


class FormattersManager(object):
  """Class that implements the formatters manager."""

  _DEFAULT_FORMATTER = default.DefaultFormatter()

  _custom_formatter_helpers = {}

  _formatters = {}

  @classmethod
  def _ReadFormattersFile(cls, path):
    """Reads a formatters configuration file.

    Args:
      path (str): path of file that contains the formatters configuration.

    Raises:
      KeyError: if formatter class is already set for the corresponding
          data type.
    """
    formatters_file = yaml_formatters_file.YAMLFormattersFile()
    for formatter in formatters_file.ReadFromFile(path):
      for identifier in formatter.custom_helpers:
        custom_formatter_helper = cls._custom_formatter_helpers.get(
            identifier, None)
        if custom_formatter_helper:
          formatter.AddHelper(custom_formatter_helper)

      data_type = formatter.DATA_TYPE.lower()
      cls._formatters[data_type] = formatter

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
    formatter_object = cls._formatters.get(data_type, None)
    if not formatter_object:
      logger.warning('Using default formatter for data type: {0:s}'.format(
          data_type))
      formatter_object = cls._DEFAULT_FORMATTER

    return formatter_object

  @classmethod
  def ReadFormattersFromDirectory(cls, path):
    """Reads formatters from a directory.

    Args:
      path (str): path of directory that contains the formatters configuration
          files.

    Raises:
      KeyError: if formatter class is already set for the corresponding
          data type.
    """
    if not cls._formatters:
      for formatters_file_path in glob.glob(os.path.join(path, '*.yaml')):
        cls._ReadFormattersFile(formatters_file_path)

  @classmethod
  def ReadFormattersFromFile(cls, path):
    """Reads formatters from a file.

    Args:
      path (str): path of file that contains the formatters configuration.

    Raises:
      KeyError: if formatter class is already set for the corresponding
          data type.
    """
    if not cls._formatters:
      cls._ReadFormattersFile(path)

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
