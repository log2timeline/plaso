# -*- coding: utf-8 -*-
"""CSV parser plugin for M365 Activity log."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import dsv_parser
from plaso.parsers import manager

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

class M365ActivityLogParser(dsv_parser.DSVParser):
  """Parse M365 Activity log from CSV files."""  

  NAME = 'm365_activitylog'
  DATA_FORMAT = 'M365 Activity log'

  COLUMNS = (
            'Event ID',
            'Category',
            'Description',
            'User',
            'User Principle Name',
            'App',
            'Device',
            'Location',
            'Date',
            'IP address',
            'User agent',
            'Organizations'
  )

  # List of accepted activities ...
  _ACTIVITIES = frozenset([
                          'Access file',
                          'Create folder',
                          'Download file',
                          'Failed log on',
                          'Log on',
                          'Modify file',
                          'Modify folder',
                          'Move file',
                          'Rename file',
                          'Rename folder',
                          'Share file',
                          'Sync file download',
                          'Sync file upload',
                          'Trash file',
                          'Trash folder',
                          'Unspecified',
                          'Upload file',
  ])

  _MINIMUM_NUMBER_OF_COLUMNS = 12

  _ENCODING = 'utf-8'

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      row_offset (int): line number of the row.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """
    timestamp = row.get('Date', None)
    if timestamp == 'Date':
      return

    activity = row.get('Category', None)
    if activity not in self._ACTIVITIES:
      return

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromDateTimeString(timestamp)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('invalid date time value')
      date_time = None

    event_data = M365ActivityLogEventData()
    event_data.timestamp = date_time
    event_data.description = row['Description']
    event_data.application = row['App']
    event_data.userprincipalname = row['User Principle Name']
    event_data.useragent = row['User agent']
    event_data.ipaddress = row['IP address']

    parser_mediator.ProduceEventData(event_data)

  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if len(row) != self._MINIMUM_NUMBER_OF_COLUMNS:
      return False

    # Check the date format
    # If it doesn't parse, then this isn't a M365 Activity log file.
    timestamp_value = row.get('Date', None)
    if timestamp_value != 'Date':
      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDateTimeString(timestamp_value)
      except (TypeError, ValueError):
        return False

    return True

manager.ParsersManager.RegisterParser(M365ActivityLogParser)
