# -*- coding: utf-8 -*-
"""The date-less log format helper mix-in."""

import datetime
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import events


class DateLessLogFormatHelper(object):
  """Date-less log format helper mix-in."""

  _VALID_DAYS = frozenset(range(1, 32))

  _VALID_MONTHS = frozenset(range(1, 13))

  def __init__(self):
    """Initializes the date-less log format helper mix-in."""
    super(DateLessLogFormatHelper, self).__init__()
    self._maximum_date = None
    self._minimum_date = None
    self._date = None

  def _GetDatesFromFileEntry(self, file_entry):
    """Retrieves the dates from the file entry date and time values.

    Args:
      file_entry (dfvfs.FileEntry): file entry.

    Returns:
      set[datetime.datetime]: dates of the file entry.
    """
    dates = set()

    for attribute_name in ('change_time', 'creation_time', 'modification_time'):
      date_time = getattr(file_entry, attribute_name, None)
      if date_time:
        year, month, day = date_time.GetDate()
        new_date = datetime.datetime(year, month, day)
        dates.add(new_date)

    return dates

  def _GetDate(self):
    """Retrieves the date.

    Returns:
      datetime.datetime: date.
    """
    return self._date

  def _SetDate(self, year, month, day):
    """Sets the date.

    Args:
      year (int): year.
      month (int): month.
      day (int): day.

    Raise:
      ValueError: if month or day contains an unsupported value.
    """
    if day not in self._VALID_DAYS:
      raise ValueError('Invalid day: {0!s}'.format(day))

    if month not in self._VALID_MONTHS:
      raise ValueError('Invalid month: {0!s}'.format(month))

    date = datetime.datetime(year, month, day)
    self._date = date

  def _SetEstimatedDate(self, parser_mediator):
    self._maximum_date = None
    self._minimum_date = None
    self._date = None

    dates = set()

    file_entry = parser_mediator.GetFileEntry()
    if file_entry:
      dates = self._GetDatesFromFileEntry(file_entry)

    if not dates and file_entry.type_indicator in (
        dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
        dfvfs_definitions.TYPE_INDICATOR_GZIP):

      parent_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
          file_entry.path_spec.parent,
          resolver_context=parser_mediator.resolver_context)
      if parent_file_entry:
        dates = self._GetDatesFromFileEntry(parent_file_entry)

    if dates:
      self._maximum_date = max(dates)
      self._minimum_date = min(dates)
      self._date = self._minimum_date

  def GetDateLessLogHelper(self):
    """Retrieves a date-less log helper attribute container.

    Returns:
      DateLessLogHelper: date-less log helper.
    """
    date_less_log_helper = events.DateLessLogHelper()
    date_less_log_helper.latest_date = self._maximum_date
    date_less_log_helper.earliest_date = self._minimum_date

    return date_less_log_helper
