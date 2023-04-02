# -*- coding: utf-8 -*-
"""Parser for McAfee Anti-Virus Logs.

McAfee AV uses 4 logs to track when scans were run, when virus databases were
updated, and when files match the virus database.

"""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import dsv_parser
from plaso.parsers import manager


class McafeeAVEventData(events.EventData):
  """McAfee AV Log event data.

  Attributes:
    action (str): action.
    filename (str): filename.
    offset (int): offset of the line relative to the start of the file, from
        which the event data was extracted.
    rule (str): rule.
    status (str): status.
    trigger_location (str): trigger location.
    username (str): username.
    written_time (dfdatetime.DateTimeValues): entry written date and time.
  """

  DATA_TYPE = 'av:mcafee:accessprotectionlog'

  def __init__(self):
    """Initializes event data."""
    super(McafeeAVEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.filename = None
    self.offset = None
    self.rule = None
    self.status = None
    self.trigger_location = None
    self.username = None
    self.written_time = None


class McafeeAccessProtectionParser(dsv_parser.DSVParser):
  """Parses the McAfee AV Access Protection Log."""

  NAME = 'mcafee_protection'
  DATA_FORMAT = 'McAfee Anti-Virus access protection log file'

  DELIMITER = '\t'
  COLUMNS = [
      'date', 'time', 'status', 'username', 'filename',
      'trigger_location', 'rule', 'action']

  _ENCODING = 'utf-8'

  _NUMBER_OF_COLUMNS = len(COLUMNS)

  def _CreateDateTime(self, date_string, time_string):
    """Creates a date time value from the date time strings.

    The format stores the date and time as 2 separate strings separated by
    a tab. The time is in local time. The month and day can be either 1 or 2
    characters long, for example: "7/30/2013\\t10:22:48 AM"

    Args:
      date_string (str): date string.
      time_string (str): time string.

    Returns:
      dfdatetime.TimeElements: date time object.

    Raises:
      ParseError: if the date or time string cannot be converted in
          a date time object.
    """
    if not date_string and not time_string:
      raise errors.ParseError('Missing date or time string.')

    # TODO: Figure out how McAfee sets Day First and use that here.
    # The in-file time format is '07/30/2013\t10:22:48 AM'.

    try:
      month_string, day_of_month_string, year_string = date_string.split('/')
      year = int(year_string, 10)
      month = int(month_string, 10)
      day_of_month = int(day_of_month_string, 10)
    except (AttributeError, ValueError):
      raise errors.ParseError('Unsupported date string: {0:s}'.format(
          date_string))

    try:
      time_value, time_suffix = time_string.split(' ')
      hours_string, minutes_string, seconds_string = time_value.split(':')
      hours = int(hours_string, 10)
      minutes = int(minutes_string, 10)
      seconds = int(seconds_string, 10)
    except (AttributeError, ValueError):
      raise errors.ParseError('Unsupported time string: {0:s}'.format(
          time_string))

    if time_suffix == 'PM':
      hours += 12
    elif time_suffix != 'AM':
      raise errors.ParseError('Unsupported time suffix: {0:s}.'.format(
          time_suffix))

    time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)

    except ValueError:
      raise errors.ParseError(
          'Unsupported date and time strings: {0:s} {1:s}'.format(
              date_string, time_string))

    date_time.is_local_time = True
    return date_time

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): offset of the line from which the row was extracted.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """
    try:
      date_time = self._CreateDateTime(row['date'], row['time'])
    except errors.ParseError as exception:
      parser_mediator.ProduceExtractionWarning(
          'Unable to create date time with error: {0!s}'.format(exception))
      date_time = None

    status = row['status']
    if status:
      status = status.rstrip()

    event_data = McafeeAVEventData()
    event_data.action = row['action']
    event_data.filename = row['filename']
    event_data.offset = row_offset
    event_data.rule = row['rule']
    event_data.status = status
    event_data.trigger_location = row['trigger_location']
    event_data.username = row['username']
    event_data.written_time = date_time

    parser_mediator.ProduceEventData(event_data)

  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if len(row) != self._NUMBER_OF_COLUMNS:
      return False

    # If the date and time string cannot be converted into a date time object,
    # then do not consider this to be a McAfee AV Access Protection Log.
    try:
      self._CreateDateTime(row['date'], row['time'])
    except errors.ParseError:
      return False

    # Use the presence of these strings as a backup or in case of partial file.
    status = row['status']
    if 'Access Protection' not in status and 'Would be blocked' not in status:
      return False

    return True


manager.ParsersManager.RegisterParser(McafeeAccessProtectionParser)
