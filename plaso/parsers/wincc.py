# -*- coding: utf-8 -*-
"""Text parser plugin for WinCC log files."""

from dfvfs.helpers import text_file

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class SIMATICS7EventData(events.EventData):
  """SIMATIC S7 event data.

  Attributes:
    body (str): the message content of the event.
    creation_time (dfdatetime.DateTimeValues): date and time the log entry
        was created.
  """

  DATA_TYPE = 'wincc:simatic_s7:entry'

  def __init__(self):
    """Initializes event data."""
    super(SIMATICS7EventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.creation_time = None


class WinCCSysLogEventData(events.EventData):
  """WinCC Sys Log event data.

  Attributes:
    body (str): the content of the log's message.
    creation_time (dfdatetime.DateTimeValues): date and time the log entry
        was created.
    event_number (int): a number specifying the type of event.
    log_hostname (str): the hostname of the machine logging the event.
    log_identifier (int): identifier for this log file.
    source_device (str): which device generated the event.
  """

  DATA_TYPE = 'wincc:sys_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(WinCCSysLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.creation_time = None
    self.event_number = None
    self.log_hostname = None
    self.log_identifier = None
    self.source_device = None


class SIMATICLogParser(interface.FileObjectParser):
  """Text parser plugin for SIMATIC S7 Log files."""

  NAME = 'simatic_s7'
  DATA_FORMAT = 'SIMATIC S7 Log file'

  DELIMITER = ','
  ENCODING = 'ascii'
  END_OF_LINE = '\r\n'

  _EXPECTED_FIRST_LINE_STRING = 'Log starting ...' + END_OF_LINE
  _EXPECTED_SECOND_LINE_STRING = '| LogFileName'
  _EXPECTED_THIRD_LINE_STRING = '| LogFileCount'

  def _ParseValues(self, parser_mediator, line_number, values):
    """Parses SIMATIC S7 log file values.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      line_number (int): number of the line the values were extracted from.
      values (list[str]): values extracted from the line.

    Raises:
      WrongParser: when the values cannot be parsed.
    """
    number_of_values = len(values)
    if number_of_values < 2:
      error_string = 'Expected at least two values on line {0:d}'.format(
          line_number)
      raise errors.WrongParser(error_string)

    # The first lines seem to  always follow the following format:
    #
    # 2019-05-27 10:05:43,405 INFO     Log starting ...
    # 2019-05-27 10:05:43,405 INFO     | LogFileName   : C:\.....
    # 2019-05-27 10:05:43,419 INFO     | LogFileCount  : 3
    if line_number == 0:
      if not values[1].endswith(self._EXPECTED_FIRST_LINE_STRING):
        error_string = 'Expected first line to end with "{0:s}"."{1!s}"'.format(
            self._EXPECTED_FIRST_LINE_STRING, values[1])
        raise errors.WrongParser(error_string)

    if line_number == 1:
      if values[1].find(self._EXPECTED_SECOND_LINE_STRING) < 0:
        error_string = 'Expected second line to contain "{0:s}"'.format(
            self._EXPECTED_SECOND_LINE_STRING)
        raise errors.WrongParser(error_string)

    if line_number == 2:
      if values[1].find(self._EXPECTED_THIRD_LINE_STRING) < 0:
        error_string = 'Expected third line to contain {0:s}'.format(
            self._EXPECTED_THIRD_LINE_STRING)
        raise errors.WrongParser(error_string)

    event_data = SIMATICS7EventData()
    try:
      date_time = dfdatetime_time_elements.TimeElements()
      date_time.CopyFromDateTimeString(values[0])
      event_data.creation_time = date_time
    except (TypeError, ValueError) as exception:
      error_string = (
          'Unable to parse date time value with error: '
          '{0!s} on line {1:d} {2!s}').format(exception, line_number, values)
      parser_mediator.ProduceExtractionWarning(error_string)

    event_data.body = ','.join(values[1:]).strip()

    parser_mediator.ProduceEventData(event_data)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a SIMATIC Log file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    line_reader = text_file.TextFile(
        file_object, encoding=self.ENCODING, end_of_line=self.END_OF_LINE)

    line_number = 0

    try:
      line = line_reader.readline()
    except UnicodeDecodeError as exception:
      raise errors.WrongParser(
          'unable to read line: {0:d} with error: {1!s}'.format(
              line_number, exception))

    while line:
      values = line.split(self.DELIMITER)
      self._ParseValues(parser_mediator, line_number, values)

      try:
        line_number += 1
        line = line_reader.readline()
      except UnicodeDecodeError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to read line: {0:d} with error: {1!s}'.format(
                line_number, exception))
        break


class WinCCSysLogParser(interface.FileObjectParser):
  """Text parser plugin for WinCC Sys Log files."""

  NAME = 'wincc_sys'
  DATA_FORMAT = 'WinCC Sys Log file'

  DELIMITER = ','
  ENCODING = 'utf-16-le'

  _DISALLOWED_HOSTNAME_CHARS = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']

  _END_OF_LOG_FILE_STRING = '======>'

  def _ParseValues(self, parser_mediator, line_number, values, first_line):
    """Parses WinCC log file values.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      line_number (int): number of the line the values were extracted from.
      values (list[str]): values extracted from the line.
      first_line (bool): True if this is first line from which values were
          extracted.

    Raises:
      WrongParser: when the values cannot be parsed.
    """
    number_of_values = len(values)
    if len(values) < 10:
      error_string = 'invalid number of values : {0:d} in line: {1:d}'.format(
          number_of_values, line_number)

      # On other lines, we might encounter times where the split() operation
      # produces more values.
      if first_line:
        raise errors.WrongParser(error_string)

      parser_mediator.ProduceExtractionWarning(error_string)

    event_data = WinCCSysLogEventData()

    try:
      log_identifier = int(values[0], 10)
      event_data.log_identifier = log_identifier
    except ValueError as exception:
      error_string = (
          'Type of first value ({0!s}) should be an int in line: {1:d}').format(
              values[0], line_number)
      self._ParseValuesFail(
          parser_mediator, first_line, exception, error_string)

    try:
      date_string = values[1]
      time_string = values[2]
      day_of_month, month, year = [
          int(element, 10) for element in date_string.split('.')]
      hours, minutes, seconds, milliseconds = [
          int(element, 10) for element in time_string.split(':')]
      time_elements_tuple = (
          year, month, day_of_month, hours, minutes, seconds, milliseconds)
      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple,
      )
      # Unsure about whether the format is dependant on the system's Locale
      date_time.is_local_time = True

      event_data.creation_time = date_time

    except (TypeError, ValueError) as exception:
      error_string = (
          'Unable to parse time elements with error: '
          '{0!s} on line {1:d} {2!s}').format(
              exception, line_number, values[1:2])
      self._ParseValuesFail(
          parser_mediator, first_line, exception, error_string)

    try:
      event_data.event_number = int(values[3], 10)
    except ValueError as exception:
      error_string = (
          'Type of event_number value ({0!s}) should be a decimal in line:'
          '{1:d}').format(values[3], line_number)
      self._ParseValuesFail(
          parser_mediator, first_line, exception, error_string)

    # Column 4 and 5 contain unknown values, we are not parsing them.

    # We are checking this only once, on the first line, as we expect all
    # following lines to contain the same hostname, as the logs are
    # collected from the system generating it.
    # Using this documentation to validate a Windows host name.
    # https://learn.microsoft.com/en-us/troubleshoot/windows-server/identity/naming-conventions-for-computer-domain-site-ou
    hostname = values[6]
    if first_line:
      if not hostname:
        error_string = (
            'Hostname ({0!s}) needs to be at least 1 character on line:'
            '{1:d}').format(hostname, line_number)
        self._ParseValuesFail(
            parser_mediator, first_line, exception, error_string)
      if len(hostname) > 16:
        error_string = (
            'Hostname ({0!s}) can\'t be longer than 15 characters on line:'
            '{1:d}').format(hostname, line_number)
        self._ParseValuesFail(
            parser_mediator, first_line, exception, error_string)
      for character in self._DISALLOWED_HOSTNAME_CHARS:
        if character in hostname:
          error_string = (
              'Hostname ({0!s}) can\'t contain the character {1:s} on line'
              '{2:d}').format(hostname, character, line_number)
          self._ParseValuesFail(
              parser_mediator, first_line, exception, error_string)

    event_data.log_hostname = hostname

    event_data.source_device = values[7]

    # The second to last field is the one that might contain unquoted separator.
    # The last field can contain a string such as MSG_STATE_COME, MSG_STATE_GO,
    # but also sometimes contains a message string.

    text_message = ' '.join(values[8:])
    event_data.body = text_message

    parser_mediator.ProduceEventData(event_data)

  def _ParseValuesFail(
      self, parser_mediator, first_line, parent_exception, error_string):
    if first_line:
      raise errors.WrongParser(error_string) from parent_exception

    parser_mediator.ProduceExtractionWarning(error_string)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a WinCC Sys Log file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    # Note that we cannot use the DSVParser here since this WinCC file format is
    # not strict and clean file format.
    line_reader = text_file.TextFile(
        file_object, encoding=self.ENCODING, end_of_line='\r\n')

    line_number = 0
    first_line = True

    # While the file is in UTF-16, the end_of_line character is '\r\n'.
    # We manually strip this out.

    try:
      line = line_reader.readline().strip()
    except UnicodeDecodeError as exception:
      raise errors.WrongParser(
          'unable to read line: {0:d} with error: {1!s}'.format(
              line_number, exception))

    while line:
      if line.startswith(self._END_OF_LOG_FILE_STRING):
        # It seems that sometimes WinCC logs will end with a line starting like
        # this, with the name of the next log file.
        # But this is not always the case though.
        line = line_reader.readline().strip()
        continue
      values = line.split(self.DELIMITER)
      self._ParseValues(parser_mediator, line_number, values, first_line)

      try:
        line_number += 1
        first_line = False
        line = line_reader.readline().strip()
      except UnicodeDecodeError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to read line: {0:d} with error: {1!s}'.format(
                line_number, exception))
        break


manager.ParsersManager.RegisterParsers([WinCCSysLogParser, SIMATICLogParser])
