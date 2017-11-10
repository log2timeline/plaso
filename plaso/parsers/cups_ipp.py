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

Also see:
* https://github.com/libyal/assorted/blob/master/documentation/
  CUPS%20Internet%20Printing%20Protocol%20format.asciidoc
"""

from __future__ import unicode_literals

import logging

import construct

from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import rfc2579_date_time as dfdatetime_rfc2579_date_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


# TODO: RFC Pendings types: resolution, dateTime, rangeOfInteger.
#       "dateTime" is not used by Mac OS, instead it uses integer types.
# TODO: Only tested against CUPS IPP Mac OS X.


class CupsIppEventData(events.EventData):
  """CUPS IPP event data.

  Attributes:
    application (str): application that prints the document.
    data_dict (dict[str, object]): parsed data coming from the file.
    computer_name (str): name of the computer.
    copies (int): number of copies.
    doc_type (str): type of document.
    job_id (str): job identifier.
    job_name (str): job name.
    owner (str): real name of the user.
    printer_id (str): identification name of the print.
    uri (str): URL of the CUPS service.
    user (str): system user name.
  """

  DATA_TYPE = 'cups:ipp:event'

  def __init__(self):
    """Initializes event data."""
    super(CupsIppEventData, self).__init__(data_type=self.DATA_TYPE)
    self.application = None
    # TODO: remove data_dict.
    self.data_dict = None
    self.computer_name = None
    self.copies = None
    self.data_dict = None
    self.doc_type = None
    self.job_id = None
    self.job_name = None
    self.owner = None
    self.printer_id = None
    self.uri = None
    self.user = None


class CupsIppParser(interface.FileObjectParser):
  """Parser for CUPS IPP files. """

  NAME = 'cups_ipp'
  DESCRIPTION = 'Parser for CUPS IPP files.'

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
      'cups_ipp_header_struct',
      construct.UBInt8('major_version'),
      construct.UBInt8('minor_version'),
      construct.UBInt16('operation_id'),
      construct.UBInt32('request_id'))

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
  INTEGER_8 = construct.UBInt8('integer')
  INTEGER_32 = construct.UBInt32('integer')
  TEXT = construct.PascalString(
      'text',
      length_field=construct.UBInt8('length'))
  BOOLEAN = construct.Struct(
      'boolean_value',
      construct.Padding(1),
      INTEGER_8)
  INTEGER = construct.Struct(
      'integer_value',
      construct.Padding(1),
      INTEGER_32)

  # This is an RFC2579 datetime.
  DATETIME = construct.Struct(
      'datetime',
      construct.Padding(1),
      construct.UBInt16('year'),
      construct.UBInt8('month'),
      construct.UBInt8('day'),
      construct.UBInt8('hour'),
      construct.UBInt8('minutes'),
      construct.UBInt8('seconds'),
      construct.UBInt8('deciseconds'),
      construct.String('direction_from_utc', length=1, encoding='ascii'),
      construct.UBInt8('hours_from_utc'),
      construct.UBInt8('minutes_from_utc'),
  )

  # Name of the pair.
  PAIR_NAME = construct.Struct(
      'pair_name',
      TEXT,
      construct.Padding(1))

  # Specific CUPS IPP to generic name.
  _NAME_PAIR_TRANSLATION = {
      'com.apple.print.JobInfo.PMApplicationName': 'application',
      'com.apple.print.JobInfo.PMJobOwner': 'owner',
      'DestinationPrinterID': 'printer_id',
      'document-format': 'doc_type',
      'job-name': 'job_name',
      'job-originating-host-name': 'computer_name',
      'job-originating-user-name': 'user',
      'job-uuid': 'job_id',
      'printer-uri': 'uri'}

  _DATE_TIME_VALUES = {
      'date-time-at-creation': definitions.TIME_DESCRIPTION_CREATION,
      'date-time-at-processing': definitions.TIME_DESCRIPTION_START,
      'date-time-at-completed': definitions.TIME_DESCRIPTION_END}

  _POSIX_TIME_VALUES = {
      'time-at-creation': definitions.TIME_DESCRIPTION_CREATION,
      'time-at-processing': definitions.TIME_DESCRIPTION_START,
      'time-at-completed': definitions.TIME_DESCRIPTION_END}

  _DATE_TIME_VALUE_NAMES = list(_DATE_TIME_VALUES.keys())
  _DATE_TIME_VALUE_NAMES.extend(list(_POSIX_TIME_VALUES.keys()))

  def _GetStringValue(self, data_dict, name, default_value=None):
    """Retrieves a specific string value from the data dict.

    Args:
      data_dict (dict[str, list[str]): values per name.
      name (str): name of the value to retrieve.

    Returns:
      str: value represented as a string.
    """
    values = data_dict.get(name, None)
    if not values:
      return default_value

    for index, value in enumerate(values):
      if ',' in value:
        values[index] = '"{0:s}"'.format(value)

    return ', '.join(values)

  def _ReadPair(self, parser_mediator, file_object):
    """Reads an attribute name and value pair from a CUPS IPP event.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Returns:
      tuple: contains:

        str: name or None.
        str: value or None.
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
      self.INTEGER_8.parse_stream(file_object)

    except (IOError, construct.FieldError) as exception:
      parser_mediator.ProduceExtractionError(
          'unable to parse pair identifier with error: {0!s}'.format(
              exception))
      return None, None

    # Name = Length name + name + 0x00
    try:
      pair_name = self.PAIR_NAME.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      parser_mediator.ProduceExtractionError(
          'unable to parse pair name with error: {0!s}'.format(exception))
      return None, None

    try:
      name = pair_name.text.decode('utf-8')
    except UnicodeDecodeError as exception:
      parser_mediator.ProduceExtractionError(
          'unable to decode pair name with error: {0!s}'.format(exception))
      return None, None

    # Value: can be integer, boolean or text select by Type ID.
    if type_id in (
        self.TYPE_GENERAL_INTEGER, self.TYPE_INTEGER, self.TYPE_ENUMERATION):
      value_structure = self.INTEGER
    elif type_id == self.TYPE_BOOL:
      value_structure = self.BOOLEAN
    elif type_id == self.TYPE_DATETIME:
      value_structure = self.DATETIME
    else:
      value_structure = self.TEXT

    try:
      value = value_structure.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      parser_mediator.ProduceExtractionError(
          'unable to parse value with error: {0!s}'.format(exception))
      return None, None

    if type_id in (
        self.TYPE_GENERAL_INTEGER, self.TYPE_INTEGER, self.TYPE_ENUMERATION):
      value = value.integer

    elif type_id == self.TYPE_BOOL:
      value = bool(value.integer)

    elif type_id == self.TYPE_DATETIME:
      rfc2579_date_time_tuple = (
          value.year, value.month, value.day, value.hour,
          value.minutes, value.seconds, value.deciseconds,
          value.direction_from_utc, value.hours_from_utc,
          value.minutes_from_utc)
      value = dfdatetime_rfc2579_date_time.RFC2579DateTime(
          rfc2579_date_time_tuple=rfc2579_date_time_tuple)

    else:
      try:
        value = value.decode('utf-8')
      except UnicodeDecodeError as exception:
        parser_mediator.ProduceExtractionError(
            'unable to decode value with error: {0!s}'.format(exception))
        return None, None

    return name, value

  def _ReadPairs(self, parser_mediator, file_object):
    """Reads the attribute name and value pairs from a CUPS IPP event.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Returns:
      dict[str, list[str]]: values per name.
    """
    data_dict = {}

    name, value = self._ReadPair(parser_mediator, file_object)
    while name or value:
      # Translate the known "name" CUPS IPP to a generic name value.
      pretty_name = self._NAME_PAIR_TRANSLATION.get(name, name)
      data_dict.setdefault(pretty_name, []).append(value)
      name, value = self._ReadPair(parser_mediator, file_object)

    return data_dict

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a CUPS IPP file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    try:
      header = self.CUPS_IPP_HEADER.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          'Unable to parse CUPS IPP Header with error: {0!s}'.format(
              exception))

    if (header.major_version != self.IPP_MAJOR_VERSION or
        header.minor_version != self.IPP_MINOR_VERSION):
      raise errors.UnableToParseFile(
          '[{0:s}] Unsupported version number.'.format(self.NAME))

    if header.operation_id != self.IPP_OP_ID:
      # Warn if the operation ID differs from the standard one. We should be
      # able to parse the file nonetheless.
      logging.debug(
          '[{0:s}] Unsupported operation identifier in file: {1:s}.'.format(
              self.NAME, parser_mediator.GetDisplayName()))

    data_dict = self._ReadPairs(parser_mediator, file_object)

    time_dict = {}

    for name in self._DATE_TIME_VALUE_NAMES:
      value = data_dict.get(name, None)
      if value is not None:
        time_dict[name] = value
        del data_dict[name]

    event_data = CupsIppEventData()
    event_data.application = self._GetStringValue(data_dict, 'application')
    event_data.computer_name = self._GetStringValue(data_dict, 'computer_name')
    event_data.copies = data_dict.get('copies', [0])[0]
    event_data.data_dict = data_dict
    event_data.doc_type = self._GetStringValue(data_dict, 'doc_type')
    event_data.job_id = self._GetStringValue(data_dict, 'job_id')
    event_data.job_name = self._GetStringValue(data_dict, 'job_name')
    event_data.user = self._GetStringValue(data_dict, 'user')
    event_data.owner = self._GetStringValue(data_dict, 'owner')
    event_data.printer_id = self._GetStringValue(data_dict, 'printer_id')
    event_data.uri = self._GetStringValue(data_dict, 'uri')

    for name, usage in iter(self._DATE_TIME_VALUES.items()):
      time_values = time_dict.get(name, [])
      for date_time in time_values:
        event = time_events.DateTimeValuesEvent(date_time, usage)
        parser_mediator.ProduceEventWithEventData(event, event_data)

    for name, usage in iter(self._POSIX_TIME_VALUES.items()):
      time_values = time_dict.get(name, [])
      for time_value in time_values:
        date_time = dfdatetime_posix_time.PosixTime(timestamp=time_value)
        event = time_events.DateTimeValuesEvent(date_time, usage)
        parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(CupsIppParser)
