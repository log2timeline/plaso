# -*- coding: utf-8 -*-
"""The logging filter classes."""

import logging


class LoggingFilter(logging.Filter):
  """Logging filter.

  Some libraries, like binplist, introduce excessive amounts of
  logging that clutters the debug logs of plaso, making them
  almost unusable. This class implements a filter designed to make
  the debug logs more clutter-free.
  """

  def filter(self, record):
    """Filter messages sent to the logging infrastructure.

    Returns:
      bool: True if the record should be included in the logging.
    """
    if record.module == u'binplist' and record.levelno < logging.ERROR:
      return False

    return True
