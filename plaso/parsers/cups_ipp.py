# -*- coding: utf-8 -*-
"""The CUPS IPP Control Files Parser.

CUPS IPP version 1.0:
* http://tools.ietf.org/html/rfc2565
* http://tools.ietf.org/html/rfc2566
* http://tools.ietf.org/html/rfc2567
* http://tools.ietf.org/html/rfc2568
* http://tools.ietf.org/html/rfc2569
* http://tools.ietf.org/html/rfc2639

CUPS IPP version 1.1:
* http://tools.ietf.org/html/rfc2910
* http://tools.ietf.org/html/rfc2911
* http://tools.ietf.org/html/rfc3196
* http://tools.ietf.org/html/rfc3510

CUPS IPP version 2.0:
* N/A
"""

import logging

import construct

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


# TODO: RFC Pendings types: resolution, dateTime, rangeOfInteger.
#       "dateTime" is not used by Mac OS, instead it uses integer types.
# TODO: Only tested against CUPS IPP Mac OS X.


class CupsIppEvent(time_events.TimestampEvent):
  """Convenience class for an cups ipp event."""

  DATA_TYPE = u'cups:ipp:event'

  def __init__(self, timestamp, timestamp_description, data_dict):
    """Initializes the event object.

    Args:
      timestamp: the timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      timestamp_description: The usage string for the timestamp value.
      data_dict: Dictionary with all the pairs coming from IPP file.
        user: String with the system user name.
        owner: String with the real name of the user.
        computer_name: String with the name of the computer.
        printer_id: String with the identification name of the print.
        uri: String with the URL of the CUPS service.
        job_id: String with the identification id of the job.
        job_name: String with the job name.
        copies: Integer with the number of copies.
        application: String with the application that prints the document.
        doc_type: String with the type of document.
        data_dict: Dictionary with all the parsed data coming from the file.
    """
    super(CupsIppEvent, self).__init__(timestamp, timestamp_description)
    # TODO: Find a better solution than to have join for each attribute.
    self.user = self._ListToString(data_dict.get(u'user', None))
    self.owner = self._ListToString(data_dict.get(u'owner', None))
    self.computer_name = self._ListToString(data_dict.get(
        u'computer_name', None))
    self.printer_id = self._ListToString(data_dict.get(u'printer_id', None))
    self.uri = self._ListToString(data_dict.get(u'uri', None))
    self.job_id = self._ListToString(data_dict.get(u'job_id', None))
    self.job_name = self._ListToString(data_dict.get(u'job_name', None))
    self.copies = data_dict.get(u'copies', 0)[0]
    self.application = self._ListToString(data_dict.get(u'application', None))
    self.doc_type = self._ListToString(data_dict.get(u'doc_type', None))
    self.data_dict = data_dict

  def _ListToString(self, values):
    """Returns a string from a list value using comma as a delimiter.

    If any value inside the list contains comma, which is the delimiter,
    the entire field is surrounded with double quotes.

    Args:
      values: A list or tuple containing the values.

    Returns:
      A string containing all the values joined using comma as a delimiter
      or None.
    """
    if values is None:
      return

    if not isinstance(values, (list, tuple)):
      return

    for index, value in enumerate(values):
      if u',' in value:
        values[index] = u'"{0:s}"'.format(value)

    try:
      return u', '.join(values)
    except UnicodeDecodeError as exception:
      logging.error(
          u'Unable to parse log line, with error: {0:s}'.format(exception))


class CupsIppParser(interface.FileObjectParser):
  """Parser for CUPS IPP files. """

  NAME = u'cups_ipp'
  DESCRIPTION = u'Parser for CUPS IPP files.'

  # INFO:
  # For each file, we have only one document with three different timestamps:
  # Created, process and finished.
  # Format:
  # [HEADER: MAGIC + KNOWN_TYPE][GROUP A]...[GROUP Z][GROUP_END: 0x03]
  # GROUP: [GROUP ID][PAIR A]...[PAIR Z] where [PAIR: NAME + VALUE]
  #   GROUP ID: [1byte ID]
  #   PAIR: [TagID][\x00][Name][Value])
  #     TagID: 1 byte integer with the type of "Value".
  #     Name: [Length][Text][\00]
  #       Name can be empty when the name has more than one value.
  #       Example: family name "lopez mata" with more than one surname.
  #       Type_Text + [0x06, family, 0x00] + [0x05, lopez, 0x00] +
  #       Type_Text + [0x00, 0x00] + [0x04, mata, 0x00]
  #     Value: can be integer, boolean, or text provided by TagID.
  #       If boolean, Value: [\x01][0x00(False)] or [\x01(True)]
  #       If integer, Value: [\x04][Integer]
  #       If text,    Value: [Length text][Text][\00]

  # Magic number that identify the CUPS IPP supported version.
  IPP_MAJOR_VERSION = 2
  IPP_MINOR_VERSION = 0
  # Supported Operation ID.
  IPP_OP_ID = 5

  # CUPS IPP File header.
  CUPS_IPP_HEADER = construct.Struct(
      u'cups_ipp_header_struct',
      construct.UBInt8(u'major_version'),
      construct.UBInt8(u'minor_version'),
      construct.UBInt16(u'operation_id'),
      construct.UBInt32(u'request_id'))

  # Group ID that indicates the end of the IPP Control file.
  GROUP_END = 3
  # Identification Groups.
  GROUP_LIST = [1, 2, 4, 5, 6, 7]

  # Type ID, per cups source file ipp-support.c.
  TYPE_GENERAL_INTEGER = 0x20
  TYPE_INTEGER = 0x21
  TYPE_BOOL = 0x22
  TYPE_ENUMERATION = 0x23
  TYPE_DATETIME = 0x31

  # Type of values that can be extracted.
  INTEGER_8 = construct.UBInt8(u'integer')
  INTEGER_32 = construct.UBInt32(u'integer')
  TEXT = construct.PascalString(
      u'text',
      encoding='utf-8',
      length_field=construct.UBInt8(u'length'))
  BOOLEAN = construct.Struct(
      u'boolean_value',
      construct.Padding(1),
      INTEGER_8)
  INTEGER = construct.Struct(
      u'integer_value',
      construct.Padding(1),
      INTEGER_32)

  # This is an RFC 2579 datetime.
  DATETIME = construct.Struct(
      u'datetime',
      construct.Padding(1),
      construct.UBInt16(u'year'),
      construct.UBInt8(u'month'),
      construct.UBInt8(u'day'),
      construct.UBInt8(u'hour'),
      construct.UBInt8(u'minutes'),
      construct.UBInt8(u'seconds'),
      construct.UBInt8(u'deciseconds'),
      construct.String(u'direction_from_utc', length=1, encoding='ascii'),
      construct.UBInt8(u'hours_from_utc'),
      construct.UBInt8(u'minutes_from_utc'),
  )

  # Name of the pair.
  PAIR_NAME = construct.Struct(
      u'pair_name',
      TEXT,
      construct.Padding(1))

  # Specific CUPS IPP to generic name.
  NAME_PAIR_TRANSLATION = {
      u'printer-uri': u'uri',
      u'job-uuid': u'job_id',
      u'DestinationPrinterID': u'printer_id',
      u'job-originating-user-name': u'user',
      u'job-name': u'job_name',
      u'document-format': u'doc_type',
      u'job-originating-host-name': u'computer_name',
      u'com.apple.print.JobInfo.PMApplicationName': u'application',
      u'com.apple.print.JobInfo.PMJobOwner': u'owner'}

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a CUPS IPP file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    try:
      header = self.CUPS_IPP_HEADER.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse CUPS IPP Header with error: {0:s}'.format(
              exception))

    if (header.major_version != self.IPP_MAJOR_VERSION or
        header.minor_version != self.IPP_MINOR_VERSION):
      raise errors.UnableToParseFile(
          u'[{0:s}] Unsupported version number.'.format(self.NAME))

    if header.operation_id != self.IPP_OP_ID:
      # Warn if the operation ID differs from the standard one. We should be
      # able to parse the file nonetheless.
      logging.debug(
          u'[{0:s}] Unsupported operation identifier in file: {1:s}.'.format(
              self.NAME, parser_mediator.GetDisplayName()))

    # Read the pairs extracting the name and the value.
    data_dict = {}
    name, value = self.ReadPair(parser_mediator, file_object)
    while name or value:
      # Translate the known "name" CUPS IPP to a generic name value.
      pretty_name = self.NAME_PAIR_TRANSLATION.get(name, name)
      data_dict.setdefault(pretty_name, []).append(value)
      name, value = self.ReadPair(parser_mediator, file_object)

    # TODO: Refactor to use a lookup table to do event production.
    time_dict = {}
    for key, value in data_dict.items():
      if key.startswith(u'date-time-') or key.startswith(u'time-'):
        time_dict[key] = value
        del data_dict[key]

    if u'date-time-at-creation' in time_dict:
      event_object = CupsIppEvent(
          time_dict[u'date-time-at-creation'][0],
          eventdata.EventTimestamp.CREATION_TIME, data_dict)
      parser_mediator.ProduceEvent(event_object)

    if u'date-time-at-processing' in time_dict:
      event_object = CupsIppEvent(
          time_dict[u'date-time-at-processing'][0],
          eventdata.EventTimestamp.START_TIME, data_dict)
      parser_mediator.ProduceEvent(event_object)

    if u'date-time-at-completed' in time_dict:
      event_object = CupsIppEvent(
          time_dict[u'date-time-at-completed'][0],
          eventdata.EventTimestamp.END_TIME, data_dict)
      parser_mediator.ProduceEvent(event_object)

    if u'time-at-creation' in time_dict:
      time_value = time_dict[u'time-at-creation'][0]
      timestamp = timelib.Timestamp.FromPosixTime(time_value)
      event_object = CupsIppEvent(
          timestamp, eventdata.EventTimestamp.CREATION_TIME, data_dict)
      parser_mediator.ProduceEvent(event_object)

    if u'time-at-processing' in time_dict:
      time_value = time_dict[u'time-at-processing'][0]
      timestamp = timelib.Timestamp.FromPosixTime(time_value)
      event_object = CupsIppEvent(
          timestamp, eventdata.EventTimestamp.START_TIME, data_dict)
      parser_mediator.ProduceEvent(event_object)

    if u'time-at-completed' in time_dict:
      time_value = time_dict[u'time-at-completed'][0]
      timestamp = timelib.Timestamp.FromPosixTime(time_value)
      event_object = CupsIppEvent(
          timestamp, eventdata.EventTimestamp.END_TIME, data_dict)
      parser_mediator.ProduceEvent(event_object)

  def ReadPair(self, parser_mediator, file_object):
    """Reads an attribute name and value pair from a CUPS IPP event.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: a file-like object that points to a file.

    Returns:
      A list of name and value. If name and value cannot be read both are
      set to None.
    """
    # Pair = Type ID + Name + Value.
    try:
      # Can be:
      #   Group ID + IDtag = Group ID (1byte) + Tag ID (1byte) + '0x00'.
      #   IDtag = Tag ID (1byte) + '0x00'.
      type_id = self.INTEGER_8.parse_stream(file_object)
      if type_id == self.GROUP_END:
        return None, None

      elif type_id in self.GROUP_LIST:
        # If it is a group ID we must read the next byte that contains
        # the first TagID.
        type_id = self.INTEGER_8.parse_stream(file_object)

      # 0x00 separator character.
      _ = self.INTEGER_8.parse_stream(file_object)

    except (IOError, construct.FieldError):
      logging.warning(
          u'[{0:s}] Unsupported identifier in file: {1:s}.'.format(
              self.NAME, parser_mediator.GetDisplayName()))
      return None, None

    # Name = Length name + name + 0x00
    try:
      name = self.PAIR_NAME.parse_stream(file_object).text
    except (IOError, construct.FieldError):
      logging.warning(
          u'[{0:s}] Unsupported name in file: {1:s}.'.format(
              self.NAME, parser_mediator.GetDisplayName()))
      return None, None

    # Value: can be integer, boolean or text select by Type ID.
    try:
      if type_id in [
          self.TYPE_GENERAL_INTEGER, self.TYPE_INTEGER, self.TYPE_ENUMERATION]:
        value = self.INTEGER.parse_stream(file_object).integer

      elif type_id == self.TYPE_BOOL:
        value = bool(self.BOOLEAN.parse_stream(file_object).integer)

      elif type_id == self.TYPE_DATETIME:
        datetime = self.DATETIME.parse_stream(file_object)
        value = timelib.Timestamp.FromRFC2579Datetime(
            datetime.year, datetime.month, datetime.day, datetime.hour,
            datetime.minutes, datetime.seconds, datetime.deciseconds,
            datetime.direction_from_utc, datetime.hours_from_utc,
            datetime.minutes_from_utc)

      else:
        value = self.TEXT.parse_stream(file_object)

    except (IOError, UnicodeDecodeError, construct.FieldError):
      logging.warning(
          u'[{0:s}] Unsupported value in file: {1:s}.'.format(
              self.NAME, parser_mediator.GetDisplayName()))
      return None, None

    return name, value


manager.ParsersManager.RegisterParser(CupsIppParser)
