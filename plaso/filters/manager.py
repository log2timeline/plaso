# -*- coding: utf-8 -*-
"""This file contains the event filters manager class."""

from __future__ import unicode_literals

import logging

from plaso.lib import errors


class FiltersManager(object):
  """Filters manager."""

  _filter_classes = {}

  @classmethod
  def DeregisterFilter(cls, filter_class):
    """Deregisters a filter class.

    The filter classes are identified based on their lower case filter name.

    Args:
      filter_class (type): class object of the filter.

    Raises:
      KeyError: if filter class is not set for the corresponding filter name.
    """
    filter_name = filter_class.__name__
    if filter_name not in cls._filter_classes:
      raise KeyError(
          'Filter class not set for filter name: {0:s}.'.format(
              filter_class.__name__))

    del cls._filter_classes[filter_name]

  @classmethod
  def GetFilterObject(cls, filter_expression):
    """Creates instances of specific filters.

    Args:
      filter_expression (str): filter expression.

    Returns:
     FilterObject: the first filter found matching the filter string or
         None if no corresponding filter is available.
    """
    if not filter_expression:
      return None

    # TODO: refactor not to instantiate all filter classes.
    for filter_object in cls.GetFilterObjects():
      try:
        filter_object.CompileFilter(filter_expression)
        return filter_object

      except errors.WrongPlugin:
        logging.debug('Filter expression: {0:s} is not a filter: {1:s}'.format(
            filter_expression, filter_object.filter_name))

  @classmethod
  def GetFilterObjects(cls):
    """Creates instances of the available filters.

    Returns:
      list[FilterObject]: available filters.
    """
    return [filter_class() for filter_class in cls._filter_classes.values()]

  @classmethod
  def RegisterFilter(cls, filter_class):
    """Registers a filter class.

    The filter classes are identified based on their lower case filter name.

    Args:
      filter_class (type): class object of the filter.

    Raises:
      KeyError: if filter class is already set for the corresponding
          filter name.
    """
    filter_name = filter_class.__name__
    if filter_name in cls._filter_classes:
      raise KeyError((
          'Filter class already set for filter name: {0:s}.').format(
              filter_class.__name__))

    cls._filter_classes[filter_name] = filter_class

  @classmethod
  def RegisterFilters(cls, filter_classes):
    """Registers filter classes.

    The filter classes are identified based on their lower case filter name.

    Args:
      filter_classes (list[type]): class objects of the filters.

    Raises:
      KeyError: if filter class is already set for the corresponding
          filter name.
    """
    for filter_class in filter_classes:
      cls.RegisterFilter(filter_class)
