# -*- coding: utf-8 -*-
"""CSV parser plugin for M365 Defender UrlClickEvents table."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.lib import errors
from plaso.parsers import csv_parser
from plaso.parsers.csv_plugins import interface
from plaso.parsers.csv_plugins import dah_events

class DefenderAHUrlClickEventsPlugin(interface.CSVPlugin):
  """Parse UrlClickEvents from CSV files."""  

  NAME = 'dah_urlclickevents'
  DATA_FORMAT = 'M365 Defender UrlClickEvents table'

  # This constant is used for checking columns at CSV.
  REQUESTED_COLUMNS = {
    'Timestamp',
    'ActionType',
    'Url',
    'Workload',
    'IPAddress',
    'ThreatTypes',
    'DetectionMethods',
    'UrlChain'}

  # This constant is used for checking if they are some keywords at CSV.
  REQUESTED_CONTENT = {
    'ClickAllowed',
    'ClickBlocked',
    'ClickBlockedByTenantPolicy',
    'UrlErrorPage',
    'UrlScanInProgress'}

  _TIMESTAMP = pyparsing.pyparsing_common.iso8601_datetime

  def _ParseTimeStamp(self, date_time_string):
    """Parses date and time elements of a log line.

    Args:
      date_time_string (str): date and time elements of a log line.

    Returns:
      dfdatetime.TimeElements: date and time value.
    """
    self._TIMESTAMP.parseString(date_time_string) # pylint: disable=too-many-function-args

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
    date_time.CopyFromStringISO8601(time_string=date_time_string)
    return date_time

  def _ParseClickAllowed(self, parser_mediator, row):
    """Extracts ClickAllowed action from a CSV (Comma Separated Values) file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHClickAllowedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.url = row['url']
    event_data.workload = row['workload']
    event_data.ipaddress = row['ipaddress']
    event_data.urlchain = row['urlchain']

    parser_mediator.ProduceEventData(event_data)

  def _ParseClickBlocked(self, parser_mediator, row):
    """Extracts ClickBlocked action from a CSV (Comma Separated Values) file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHClickBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.url = row['url']
    event_data.workload = row['workload']
    event_data.ipaddress = row['ipaddress']
    event_data.urlchain = row['urlchain']
    event_data.threattypes = row['threattypes']
    event_data.detectionmethods = row['detectionmethods']

    parser_mediator.ProduceEventData(event_data)

  def _ParseClickBlockedByTenantPolicy(self, parser_mediator, row):
    """Extracts ClickBlockedByTenantPolicy action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHClickBlockedByTenantPolicyEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.url = row['url']
    event_data.workload = row['workload']
    event_data.ipaddress = row['ipaddress']
    event_data.urlchain = row['urlchain']

    parser_mediator.ProduceEventData(event_data)

  def _ParseUrlErrorPage(self, parser_mediator, row):
    """Extracts UrlErrorPage action from a CSV (Comma Separated Values) file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHUrlErrorPageEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.url = row['url']
    event_data.workload = row['workload']
    event_data.ipaddress = row['ipaddress']
    event_data.urlchain = row['urlchain']

    parser_mediator.ProduceEventData(event_data)

  def _ParseUrlScanInProgress(self, parser_mediator, row):
    """Extracts UrlScanInProgress action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHUrlScanInProgressEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.url = row['url']
    event_data.workload = row['workload']
    event_data.ipaddress = row['ipaddress']
    event_data.urlchain = row['urlchain']

    parser_mediator.ProduceEventData(event_data)

  def _ParseCsvRow(self, parser_mediator, row):
    """Extracts events from a CSV (Comma Separated Values) file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """

    try:
      tmp_row = dict((k.lower().strip(), v) for k,v in row.items())
      tmp_action = tmp_row['actiontype'].lower().strip()

      if tmp_action == 'clickallowed':
        self._ParseClickAllowed(parser_mediator, tmp_row)

      elif tmp_action == 'clickblocked':
        self._ParseClickBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'clickblockedbytenantpolicy':
        self._ParseClickBlockedByTenantPolicy(parser_mediator, tmp_row)

      elif tmp_action == 'urlerrorpage':
        self._ParseUrlErrorPage(parser_mediator, tmp_row)

      elif tmp_action == 'urlscaninoprogress':
        self._ParseUrlScanInProgress(parser_mediator, tmp_row)

    except pyparsing.ParseException as exception:
      raise errors.WrongParser(
        'unable to parse line with error: {0!s}'.format(
          exception))

csv_parser.CSVFileParser.RegisterPlugin(DefenderAHUrlClickEventsPlugin)
