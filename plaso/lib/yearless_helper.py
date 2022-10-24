# -*- coding: utf-8 -*-
"""The year-less log format helper mix-in."""

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
    self._base_year = parser_mediator.GetEstimatedYear()
    self._month = None
    self._maximum_year = parser_mediator.GetLatestYear()
    self._relative_year = 0
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
    self._maximum_year = None
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

    # Some format allow out-of-order sequences, so allow some leeway
    # to not cause Apr->May->Apr to cause the year to increment.
    # See http://bugzilla.adiscon.com/show_bug.cgi?id=527

    if self._month and (month + 1) < self._month:
      self._relative_year += 1

      if not self._maximum_year or self._year < self._maximum_year:
        self._year += 1

    self._month = month

  def GetYearLessLogHelper(self):
    """Retrieves a year-less log helper attribute container.

    Returns:
      YearLessLogHelper: year-less log helper.
    """
    year_less_log_helper = events.YearLessLogHelper()
    year_less_log_helper.estimated_creation_year = self._base_year
    # TODO: use relative_year to determine base_year

    return year_less_log_helper
