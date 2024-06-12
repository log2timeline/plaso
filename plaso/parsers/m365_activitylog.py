# -*- coding: utf-8 -*-
"""M365 Activity log (CSV) file parser."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import dsv_parser
from plaso.parsers import manager


class M365ActivityLogEventData(events.EventData):
  """M365 Activity log event data.

  Attributes:
    application (str): application of the activity.
    description (str): description of the activity..
    ip_address (str): IP address request originated from.
    recorded_time (dfdatetime.DateTimeValues): date and time when
       the activity was recorded.
    useragent (str): User agent of the activity..
    user_principal_name (str): user principle name of the activity..
  """

  DATA_TYPE = 'm365:activitylog:event'

  def __init__(self):
    """Initializes event data."""
    super(M365ActivityLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.application = None
    self.description = None
    self.ip_address = None
    self.recorded_time = None
    self.useragent = None
    self.user_principal_name = None


class M365ActivityLogParser(dsv_parser.DSVParser):
  """M365 Activity log (CSV) file parser."""

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
      'Organizations')

  _SUPPORTED_ACTIVITIES = frozenset([
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
      'Upload file'])

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
    date_value = row.get('Date', None)
    if date_value == 'Date':
      return

    activity = row.get('Category', None)
    if activity not in self._SUPPORTED_ACTIVITIES:
      return

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromDateTimeString(date_value)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning(
              f'unsupported date time value: {date_value!s}')
      date_time = None

    event_data = M365ActivityLogEventData()
    event_data.application = row['App']
    event_data.description = row['Description']
    event_data.ip_address = row['IP address']
    event_data.recorded_time = date_time
    event_data.useragent = row['User agent']
    event_data.user_principal_name = row['User Principle Name']

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

    date_value = row.get('Date', None)
    if date_value != 'Date':
      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDateTimeString(date_value)
      except (TypeError, ValueError):
        return False

    return True


manager.ParsersManager.RegisterParser(M365ActivityLogParser)
