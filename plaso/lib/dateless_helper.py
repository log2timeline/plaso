# -*- coding: utf-8 -*-
"""The date-less log format helper mix-in."""

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import events


class DateLessLogFormatHelper(object):
  """Date-less log format helper mix-in."""

  _MONTH_DICT = {
      'jan': 1,
      'feb': 2,
      'mar': 3,
      'apr': 4,
      'may': 5,
      'jun': 6,
      'jul': 7,
      'aug': 8,
      'sep': 9,
      'oct': 10,
      'nov': 11,
      'dec': 12}

  _VALID_MONTHS = frozenset(range(1, 13))

  # The date-less log format only supports time.
  _GRANULARITY_NO_DATE = 'd'

  # The date-less log format only supports month and day of month.
  _GRANULARITY_NO_YEAR = 'y'

  def __init__(self):
    """Initializes the date-less log format helper mix-in."""
    super(DateLessLogFormatHelper, self).__init__()
    self._base_date = None
    self._date = (0, 0, 0)
    self._granularity = self._GRANULARITY_NO_YEAR
    self._maximum_date = None
    self._relative_date = (0, 0, 0)

  def _GetDatesFromFileEntry(self, file_entry):
    """Retrieves the dates from the file entry date and time values.

    Args:
      file_entry (dfvfs.FileEntry): file entry.

    Returns:
      set[tuple[int, int, int]]: dates, as tuple of year, month, day, of the
          file entry.
    """
    if file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_GZIP:
      # Ignore a gzip file that contains a modification timestamp of 0.
      if (file_entry.modification_time and
          file_entry.modification_time.timestamp > 0):
        date_tuple = file_entry.modification_time.GetDate()
        return set([date_tuple])

    dates = set()

    for attribute_name in ('change_time', 'creation_time', 'modification_time'):
      date_time = getattr(file_entry, attribute_name, None)
      if date_time:
        date_tuple = date_time.GetDate()

        if (date_tuple == (1970, 1, 1) and
            file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_GZIP):
          continue

        dates.add(date_tuple)

    return dates

  def _GetMonthFromString(self, month_string):
    """Retrieves a numeric month value from a string.

    Args:
      month_string (str): month formatted as a string.

    Returns:
      int: month formatted as an integer, where January is 1.
    """
    # TODO: add support for localization.
    return self._MONTH_DICT.get(month_string.lower(), None)

  def _GetRelativeYear(self):
    """Retrieves the relative year.

    Returns:
      int: relative year.
    """
    return self._relative_date[0]

  def _GetYear(self):
    """Retrieves the year.

    Returns:
      int: year.
    """
    return self._date[0]

  def _SetEstimatedDate(self, parser_mediator):
    """Estimate the date based on the file entry dates.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
    """
    self._base_date = None
    self._date = (0, 0, 0)
    self._granularity = self._GRANULARITY_NO_DATE
    self._maximum_date = None
    self._relative_date = (0, 0, 0)

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
      self._base_date = min(dates)
      self._date = self._base_date
      self._maximum_date = max(dates)

  def _SetEstimatedYear(self, parser_mediator):
    """Estimate the year based on the file entry dates.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
    """
    self._SetEstimatedDate(parser_mediator)

    self._date = (self._date[0], 0, 0)
    self._granularity = self._GRANULARITY_NO_YEAR

  def _SetMonthAndYear(self, month, year):
    """Sets the month and year.

    Args:
      month (int): month.
      year (int): year.

    Raises:
      ValueError: if month contains an unsupported value.
    """
    if month not in self._VALID_MONTHS:
      raise ValueError('Invalid month: {0!s}'.format(month))

    self._date = (year, month, 0)
    self._granularity = self._GRANULARITY_NO_YEAR
    self._relative_date = (0, 0, 0)

  def _UpdateYear(self, month):
    """Updates the year based on the month observed in the log format.

    Args:
      month (int): month observed in the log format, where January is 1.

    Raises:
      ValueError: if month contains an unsupported value.
    """
    if month not in self._VALID_MONTHS:
      raise ValueError('Invalid month: {0!s}'.format(month))

    last_year, last_month, _ = self._date

    if last_month:
      relative_year, relative_month, relative_day_of_month = self._relative_date

      # Account for log formats that allow out-of-order date and time values
      # (Apr->May->Apr) such as rsyslog with the RepeatedMsgReduction setting
      # enabled.
      if month + 1 < last_month:
        self._relative_date = (
            relative_year + 1, relative_month, relative_day_of_month)
        last_year += 1

      # Account for out-of-order Jan->Dec->Jan with the exception of the start
      # of the log file.
      elif relative_year > 0 and last_month == 1 and month == 12:
        self._relative_date = (
            relative_year - 1, relative_month, relative_day_of_month)
        last_year -= 1

    self._date = (last_year, month, 0)

  def GetDateLessLogHelper(self):
    """Retrieves a date-less log helper attribute container.

    Returns:
      DateLessLogHelper: date-less log helper.
    """
    date_less_log_helper = events.DateLessLogHelper()
    date_less_log_helper.earliest_date = self._base_date
    date_less_log_helper.granularity = self._granularity
    date_less_log_helper.last_relative_date = self._relative_date
    date_less_log_helper.latest_date = self._maximum_date

    return date_less_log_helper
