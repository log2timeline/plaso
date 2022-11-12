# -*- coding: utf-8 -*-
"""The year-less log format helper mix-in."""

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import events


class YearLessLogFormatHelper(object):
  """Year-less log format helper mix-in."""

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

  def __init__(self):
    """Initializes the year-less log format helper mix-in."""
    super(YearLessLogFormatHelper, self).__init__()
    self._base_year = None
    self._maximum_year = None
    self._month = None
    self._relative_year = 0
    self._year = 0

  def _GetYearsFromFileEntry(self, file_entry):
    """Retrieves the years from the file entry date and time values.

    Args:
      file_entry (dfvfs.FileEntry): file entry.

    Returns:
      set[int]: years of the file entry.
    """
    years = set()

    for attribute_name in ('change_time', 'creation_time', 'modification_time'):
      date_time = getattr(file_entry, attribute_name, None)
      if date_time:
        year, _, _ = date_time.GetDate()
        years.add(year)

    return years

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
    return self._relative_year

  def _GetYear(self):
    """Retrieves the year.

    Returns:
      int: year.
    """
    return self._year

  def _SetEstimatedYear(self, parser_mediator):
    """Sets the year based on the parser mediator year estimation.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
    """
    self._base_year = None
    self._maximum_year = None
    self._month = None
    self._relative_year = 0
    self._year = 0

    years = set()

    file_entry = parser_mediator.GetFileEntry()
    if file_entry:
      years = self._GetYearsFromFileEntry(file_entry)

    if not years and file_entry.type_indicator in (
        dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
        dfvfs_definitions.TYPE_INDICATOR_GZIP):

      parent_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
          file_entry.path_spec.parent,
          resolver_context=parser_mediator.resolver_context)
      if parent_file_entry:
        years = self._GetYearsFromFileEntry(parent_file_entry)

    if years:
      self._base_year = min(years)
      self._maximum_year = max(years)
      self._year = self._base_year

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

    self._month = month
    self._relative_year = 0
    self._year = year

  def _UpdateYear(self, month):
    """Updates the year based on the month observed in the log format.

    Args:
      month (int): month observed in the log format, where January is 1.

    Raises:
      ValueError: if month contains an unsupported value.
    """
    if month not in self._VALID_MONTHS:
      raise ValueError('Invalid month: {0!s}'.format(month))

    if self._month:
      # Account for log formats that allow out-of-order date and time values
      # (Apr->May->Apr) such as rsyslog with the RepeatedMsgReduction setting
      # enabled.
      if (month + 1) < self._month:
        self._relative_year += 1
        self._year += 1

      # Account for out-of-order Jan->Dec->Jan with the exception of the start
      # of the log file.
      elif self._relative_year > 0 and self._month == 1 and month == 12:
        self._relative_year -= 1
        self._year -= 1

    self._month = month

  def GetYearLessLogHelper(self):
    """Retrieves a year-less log helper attribute container.

    Returns:
      YearLessLogHelper: year-less log helper.
    """
    year_less_log_helper = events.YearLessLogHelper()
    year_less_log_helper.earliest_year = self._base_year
    year_less_log_helper.last_relative_year = self._relative_year
    year_less_log_helper.latest_year = self._maximum_year

    return year_less_log_helper
