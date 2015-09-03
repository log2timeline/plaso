# -*- coding: utf-8 -*-
"""Parser for Windows IIS Log file.

More documentation on fields can be found here:
http://www.microsoft.com/technet/prodtechnol/WindowsServer2003/Library/
IIS/676400bc-8969-4aa7-851a-9319490a9bbb.mspx?mfr=true

"""

import logging

import pyparsing

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Ashley Holtz (ashley.a.holtz@gmail.com)'


class IISEventObject(time_events.TimestampEvent):
  """Convenience class to handle the IIS event object."""

  DATA_TYPE = u'iis:log:line'

  def __init__(self, timestamp, structure):
    """Initializes the IIS event object.

    Args:
      timestamp: The timestamp which is an interger containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      structure: The structure with any parsed log values to iterate over.
    """
    super(IISEventObject, self).__init__(
        timestamp, eventdata.EventTimestamp.WRITTEN_TIME)

    for key, value in structure.iteritems():
      if key in [u'time', u'date']:
        continue
      if value == u'-':
        continue
      if isinstance(value, pyparsing.ParseResults):
        setattr(self, key, u''.join(value))
      else:
        try:
          save_value = int(value, 10)
        except ValueError:
          save_value = value
        setattr(self, key, save_value)


class WinIISParser(text_parser.PyparsingSingleLineTextParser):
  """Parses a Microsoft IIS log file."""

  NAME = u'winiis'
  DESCRIPTION = u'Parser for Microsoft IIS log files.'

  # Common Fields (6.0: date time s-sitename s-ip cs-method cs-uri-stem
  # cs-uri-query s-port cs-username c-ip cs(User-Agent) sc-status
  # sc-substatus sc-win32-status.
  # Common Fields (7.5): date time s-ip cs-method cs-uri-stem cs-uri-query
  # s-port cs-username c-ip cs(User-Agent) sc-status sc-substatus
  # sc-win32-status time-taken

  # Define common structures.
  BLANK = pyparsing.Literal(u'-')
  WORD = pyparsing.Word(pyparsing.alphanums + u'-') | BLANK
  INT = pyparsing.Word(pyparsing.nums, min=1) | BLANK
  IP = (
      text_parser.PyparsingConstants.IPV4_ADDRESS |
      text_parser.PyparsingConstants.IPV6_ADDRESS | BLANK)
  PORT = pyparsing.Word(pyparsing.nums, min=1, max=6) | BLANK
  URI = pyparsing.Word(pyparsing.alphanums + u'/.?&+;_=()-:,%') | BLANK

  DATE_TIME = (
      pyparsing.Literal(u'#') + pyparsing.Literal(u'Date:') +
      text_parser.PyparsingConstants.DATE.setResultsName(u'date') +
      text_parser.PyparsingConstants.TIME.setResultsName(u'time'))

  COMMENT = DATE_TIME | text_parser.PyparsingConstants.COMMENT_LINE_HASH

  # Define how a log line should look like for version 6.0.
  LOG_LINE_6_0 = (
      text_parser.PyparsingConstants.DATE.setResultsName(u'date') +
      text_parser.PyparsingConstants.TIME.setResultsName(u'time') +
      URI.setResultsName(u's_sitename') + IP.setResultsName(u'dest_ip') +
      WORD.setResultsName(u'http_method') + URI.setResultsName(u'cs_uri_stem') +
      URI.setResultsName(u'cs_uri_query') + PORT.setResultsName(u'dest_port') +
      WORD.setResultsName(u'cs_username') + IP.setResultsName(u'source_ip') +
      URI.setResultsName(u'user_agent') + INT.setResultsName(u'sc_status') +
      INT.setResultsName(u'sc_substatus') +
      INT.setResultsName(u'sc_win32_status'))

  _LOG_LINE_STRUCTURES = {}

  # Common fields. Set results name with underscores, not hyphens because regex
  # will not pick them up.
  _LOG_LINE_STRUCTURES[u'date'] = (
      text_parser.PyparsingConstants.DATE.setResultsName(u'date'))
  _LOG_LINE_STRUCTURES[u'time'] = (
      text_parser.PyparsingConstants.TIME.setResultsName(u'time'))
  _LOG_LINE_STRUCTURES[u's-sitename'] = URI.setResultsName(u's_sitename')
  _LOG_LINE_STRUCTURES[u's-ip'] = IP.setResultsName(u'dest_ip')
  _LOG_LINE_STRUCTURES[u'cs-method'] = WORD.setResultsName(u'http_method')
  _LOG_LINE_STRUCTURES[u'cs-uri-stem'] = URI.setResultsName(
      u'requested_uri_stem')
  _LOG_LINE_STRUCTURES[u'cs-uri-query'] = URI.setResultsName(u'cs_uri_query')
  _LOG_LINE_STRUCTURES[u's-port'] = PORT.setResultsName(u'dest_port')
  _LOG_LINE_STRUCTURES[u'cs-username'] = WORD.setResultsName(u'cs_username')
  _LOG_LINE_STRUCTURES[u'c-ip'] = IP.setResultsName(u'source_ip')
  _LOG_LINE_STRUCTURES[u'cs(User-Agent)'] = URI.setResultsName(u'user_agent')
  _LOG_LINE_STRUCTURES[u'sc-status'] = INT.setResultsName(u'http_status')
  _LOG_LINE_STRUCTURES[u'sc-substatus'] = INT.setResultsName(u'sc_substatus')
  _LOG_LINE_STRUCTURES[u'sc-win32-status'] = (
      INT.setResultsName(u'sc_win32_status'))

  # Less common fields.
  _LOG_LINE_STRUCTURES[u's-computername'] = URI.setResultsName(
      u's_computername')
  _LOG_LINE_STRUCTURES[u'sc-bytes'] = INT.setResultsName(u'sent_bytes')
  _LOG_LINE_STRUCTURES[u'cs-bytes'] = INT.setResultsName(u'received_bytes')
  _LOG_LINE_STRUCTURES[u'time-taken'] = INT.setResultsName(u'time_taken')
  _LOG_LINE_STRUCTURES[u'cs-version'] = URI.setResultsName(u'protocol_version')
  _LOG_LINE_STRUCTURES[u'cs-host'] = URI.setResultsName(u'cs_host')
  _LOG_LINE_STRUCTURES[u'cs(Cookie)'] = URI.setResultsName(u'cs_cookie')
  _LOG_LINE_STRUCTURES[u'cs(Referrer)'] = URI.setResultsName(u'cs_referrer')
  _LOG_LINE_STRUCTURES[u'cs(Referer)'] = URI.setResultsName(u'cs_referrer')

  # Define the available log line structures. Default to the IIS v. 6.0
  # common format.
  LINE_STRUCTURES = [
      (u'comment', COMMENT),
      (u'logline', LOG_LINE_6_0)]

  # Define a signature value for the log file.
  SIGNATURE = b'#Software: Microsoft Internet Information Services'

  def __init__(self):
    """Initializes a parser object."""
    super(WinIISParser, self).__init__()
    self._date = None
    self._time = None
    self.software = None
    self.version = None

  def _ConvertToTimestamp(self, date=None, time=None):
    """Converts the given parsed date and time to a timestamp.

    Args:
      date: optional tuple or list of 3 elements for year, month, and day.
      time: optional tuple or list of 3 elements for hour, minute, and second.

    Returns:
      The timestamp which is an interger containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC.
    """
    if date:
      year, month, day = date[:3]
    else:
      return timelib.Timestamp.NONE_TIMESTAMP

    if time:
      hour, minute, second = time[:3]
    else:
      hour, minute, second = (None, None, None)

    return timelib.Timestamp.FromTimeParts(
        year, month, day, hour, minute, second)

  def _ParseCommentRecord(self, structure):
    """Parse a comment and store appropriate attributes.

    Args:
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    comment = structure[1]
    if comment.startswith(u'Version'):
      _, _, self.version = comment.partition(u':')
    elif comment.startswith(u'Software'):
      _, _, self.software = comment.partition(u':')
    elif comment.startswith(u'Date'):
      self._date = structure.get(u'date', None)
      self._time = structure.get(u'time', None)

    # Check if there's a Fields line. If not, LOG_LINE defaults to IIS 6.0
    # common format.
    elif comment.startswith(u'Fields'):
      log_line = pyparsing.Empty()
      for member in comment[7:].split():
        log_line += self._LOG_LINE_STRUCTURES.get(member, self.URI)
      # TODO: self._line_structures is a work-around and this needs
      # a structural fix.
      self._line_structures[1] = (u'logline', log_line)

  def _ParseLogLine(self, structure):
    """Parse a single log line and return an EventObject.

    Args:
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    date = structure.get(u'date', self._date)
    time = structure.get(u'time', self._time)

    timestamp = self._ConvertToTimestamp(date, time)

    return IISEventObject(timestamp, structure)

  def ParseRecord(self, unused_parser_mediator, key, structure):
    """Parse each record structure and return an event object if applicable.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.

    Returns:
      An event object (instance of EventObject) or None.
    """
    if key == u'comment':
      self._ParseCommentRecord(structure)
    elif key == u'logline':
      return self._ParseLogLine(structure)
    else:
      logging.warning(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

  def VerifyStructure(self, unused_parser_mediator, line):
    """Verify that this file is an IIS log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    # TODO: Examine other versions of the file format and if this parser should
    # support them. For now just checking if it contains the IIS header.
    if self.SIGNATURE in line:
      return True

    return False


manager.ParsersManager.RegisterParser(WinIISParser)
