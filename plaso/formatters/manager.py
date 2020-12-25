# -*- coding: utf-8 -*-
"""This file contains the event formatters manager class."""

from __future__ import unicode_literals

import glob
import os

from plaso.formatters import default
from plaso.formatters import logger
from plaso.formatters import yaml_formatters_file


class FormattersManager(object):
  """Class that implements the formatters manager."""

  _custom_formatter_helpers = {}

  _formatter_classes = {}
  _formatter_objects = {}

  # Keep track of the data types of the formatters that were read from
  # file to prevent re-reading the formatter files during unit tests and
  # so that the formatters manager can be reset to hardcoded formatters.
  _formatters_from_file = []

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
      data_type = formatter.DATA_TYPE.lower()

      custom_formatter_helper = cls._custom_formatter_helpers.get(
          data_type, None)
      if custom_formatter_helper:
        formatter.AddHelper(custom_formatter_helper)

      # TODO: refactor RegisterFormatter to only use formatter objects.
      cls.RegisterFormatter(formatter)

      cls._formatter_objects[data_type] = formatter

      cls._formatters_from_file.append(data_type)

  @classmethod
  def DeregisterFormatter(cls, formatter_class):
    """Deregisters a formatter class.

    The formatter classes are identified based on their lower case data type.

    Args:
      formatter_class (type): class of the formatter.

    Raises:
      KeyError: if formatter class is not set for the corresponding data type.
    """
    data_type = formatter_class.DATA_TYPE.lower()
    if data_type not in cls._formatter_classes:
      raise KeyError('Formatter class not set for data type: {0:s}.'.format(
          formatter_class.DATA_TYPE))

    del cls._formatter_classes[data_type]

    if data_type in cls._formatter_objects:
      del cls._formatter_objects[data_type]

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
  def ReadFormattersFromDirectory(cls, path):
    """Reads formatters from a directory.

    Args:
      path (str): path of directory that contains the formatters configuration
          files.

    Raises:
      KeyError: if formatter class is already set for the corresponding
          data type.
    """
    if not cls._formatters_from_file:
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
    if not cls._formatters_from_file:
      cls._ReadFormattersFile(path)

  @classmethod
  def RegisterEventFormatterHelper(cls, formatter_helper_class):
    """Registers a custom event formatter helper.

    The custom event formatter helpers are identified based on their lower
    case data type.

    Args:
      formatter_helper_class (type): class of the custom event formatter helper.

    Raises:
      KeyError: if a custom formatter helper is already set for the
          corresponding data type.
    """
    data_type = formatter_helper_class.DATA_TYPE.lower()
    if data_type in cls._custom_formatter_helpers:
      raise KeyError((
          'Custom event formatter helper already set for data type: '
          '{0:s}.').format(formatter_helper_class.DATA_TYPE))

    cls._custom_formatter_helpers[data_type] = formatter_helper_class()

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
    data_type = formatter_class.DATA_TYPE.lower()
    if data_type in cls._formatter_classes:
      raise KeyError('Formatter class already set for data type: {0:s}.'.format(
          formatter_class.DATA_TYPE))

    cls._formatter_classes[data_type] = formatter_class

  @classmethod
  def Reset(cls):
    """Resets the manager to the hardcoded formatter classes.

    This method is used during unit testing.
    """
    for data_type in cls._formatters_from_file:
      formatter_class = cls._formatter_objects[data_type]
      cls.DeregisterFormatter(formatter_class)

    cls._formatters_from_file = []
