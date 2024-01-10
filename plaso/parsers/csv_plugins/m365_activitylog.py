# -*- coding: utf-8 -*-
"""CSV parser plugin for M365 Activity log."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import csv_parser
from plaso.parsers.csv_plugins import interface

class M365ActivityLogEventData(events.EventData):
  """M365 Activity log event data

  Attributes:
		timestamp (dfdatetime.DateTimeValues): Date and time when
  		the event was recorded
    description (str): Description of event
    application (str): Application of event
    userprincipalname (str): User Principle Name of event
    useragent (str): User agent of event
    ipaddress (str): IP address request come from
  """

  DATA_TYPE = 'm365:activitylog:event'

  def __init__(self):
    """Initializes event data."""
    super(M365ActivityLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.timestamp = None
    self.description = None
    self.application = None
    self.userprincipalname = None
    self.useragent = None
    self.ipaddress = None

class M365ActivityLogPlugin(interface.CSVPlugin):
  """Parse M365 Activity log from CSV files."""  

  NAME = 'm365_activitylog'
  DATA_FORMAT = 'M365 Activity log'

  # This constant is used for checking columns at CSV.
  REQUESTED_COLUMNS = {
    'Description',
    'User Principle Name',
    'App',
    'Date',
    'User agent'}

  # This constant is used for checking if they are some keywords at CSV.
  REQUESTED_CONTENT = {'Access file'}

  # pylint: disable=too-many-function-args
  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
    lambda tokens: int(tokens[0], 10))

  # pylint: disable=too-many-function-args
  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
    lambda tokens: int(tokens[0], 10))

  _TIME_ZONE_OFFSET = pyparsing.Word(pyparsing.alphas, max=3)

  # 2023-10-25 17:44:53 UTC
  # pylint: disable=too-many-function-args
  _TIMESTAMP = pyparsing.Group(
    _FOUR_DIGITS + pyparsing.Suppress('-') +
    _TWO_DIGITS + pyparsing.Suppress('-') +
    _TWO_DIGITS +
    _TWO_DIGITS + pyparsing.Suppress(':') +
    _TWO_DIGITS + pyparsing.Suppress(':') +
    _TWO_DIGITS + _TIME_ZONE_OFFSET).setResultsName('timestamp')

  def _ParseTimeStamp(self, date_time_string):
    """Parses date and time elements of a log line.

    Args:
      date_time_string (str): date and time elements of a log line.

    Returns:
      dfdatetime.TimeElements: date and time value.
    """
    self._TIMESTAMP.parseString(date_time_string) # pylint: disable=too-many-function-args

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
    date_time.CopyFromDateTimeString(time_string=date_time_string)
    return date_time

  def _ParseCsvRow(self, parser_mediator, row):
    """Extracts events from a CSV (Comma Separated Values) file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.

    Raises:
      WrongParser: when the file cannot be parsed.
    """

    try:
      event_data = M365ActivityLogEventData()
      event_data.timestamp = self._ParseTimeStamp(date_time_string=row['Date'])
      event_data.description = row['Description']
      event_data.application = row['App']
      event_data.userprincipalname = row['User Principle Name']
      event_data.useragent = row['User agent']
      event_data.ipaddress = row['IP address']

      parser_mediator.ProduceEventData(event_data)

    except pyparsing.ParseException as exception:
      raise errors.WrongParser(
        'unable to parse line with error: {0!s}'.format(
        exception))

csv_parser.CSVFileParser.RegisterPlugin(M365ActivityLogPlugin)
