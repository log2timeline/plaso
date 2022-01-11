# -*- coding: utf-8 -*-
"""The CUPS IPP files parser.

CUPS IPP version 1.0:
* https://datatracker.ietf.org/doc/html/rfc2565
* https://datatracker.ietf.org/doc/html/rfc2566
* https://datatracker.ietf.org/doc/html/rfc2567
* https://datatracker.ietf.org/doc/html/rfc2568
* https://datatracker.ietf.org/doc/html/rfc2569
* https://datatracker.ietf.org/doc/html/rfc2639

CUPS IPP version 1.1:
* https://datatracker.ietf.org/doc/html/rfc2910
* https://datatracker.ietf.org/doc/html/rfc2911
* https://datatracker.ietf.org/doc/html/rfc3196
* https://datatracker.ietf.org/doc/html/rfc3510

CUPS IPP version 2.0:
* N/A
"""

import os

from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import rfc2579_date_time as dfdatetime_rfc2579_date_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


# TODO: RFC pending types: resolution, dateTime, rangeOfInteger.
#       "dateTime" is not used by Mac OS, instead it uses integer types.
# TODO: Only tested against CUPS IPP MacOS.


class CupsIppEventData(events.EventData):
  """CUPS IPP event data.

  Attributes:
    application (str): application that prints the document.
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
    self.computer_name = None
    self.copies = None
    self.doc_type = None
    self.job_id = None
    self.job_name = None
    self.owner = None
    self.printer_id = None
    self.uri = None
    self.user = None


class CupsIppParser(interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parser for CUPS IPP files."""

  NAME = 'cups_ipp'
  DATA_FORMAT = 'CUPS IPP file'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'cups_ipp.yaml')

  _SUPPORTED_FORMAT_VERSIONS = ('1.0', '1.1', '2.0')

  _DELIMITER_TAG_OPERATION_ATTRIBUTES = 0x01
  _DELIMITER_TAG_JOB_ATTRIBUTES = 0x02
  _DELIMITER_TAG_END_OF_ATTRIBUTES = 0x03
  _DELIMITER_TAG_PRINTER_ATTRIBUTES = 0x04
  _DELIMITER_TAG_UNSUPPORTED_ATTRIBUTES = 0x05

  _DELIMITER_TAGS = frozenset([
      _DELIMITER_TAG_OPERATION_ATTRIBUTES,
      _DELIMITER_TAG_JOB_ATTRIBUTES,
      _DELIMITER_TAG_PRINTER_ATTRIBUTES,
      _DELIMITER_TAG_UNSUPPORTED_ATTRIBUTES])

  _TAG_VALUE_INTEGER = 0x21
  _TAG_VALUE_BOOLEAN = 0x22
  _TAG_VALUE_ENUM = 0x23

  _TAG_VALUE_DATE_TIME = 0x31
  _TAG_VALUE_RESOLUTION = 0x32

  _TAG_VALUE_TEXT_WITHOUT_LANGUAGE = 0x41
  _TAG_VALUE_NAME_WITHOUT_LANGUAGE = 0x42

  _TAG_VALUE_KEYWORD = 0x44
  _TAG_VALUE_URI = 0x45
  _TAG_VALUE_URI_SCHEME = 0x46
  _TAG_VALUE_CHARSET = 0x47
  _TAG_VALUE_NATURAL_LANGUAGE = 0x48
  _TAG_VALUE_MEDIA_TYPE = 0x49

  _ASCII_STRING_VALUES = frozenset([
      _TAG_VALUE_KEYWORD,
      _TAG_VALUE_URI,
      _TAG_VALUE_URI_SCHEME,
      _TAG_VALUE_CHARSET,
      _TAG_VALUE_NATURAL_LANGUAGE,
      _TAG_VALUE_MEDIA_TYPE])

  _INTEGER_TAG_VALUES = frozenset([
      _TAG_VALUE_INTEGER, _TAG_VALUE_ENUM])

  _STRING_WITHOUT_LANGUAGE_VALUES = frozenset([
      _TAG_VALUE_TEXT_WITHOUT_LANGUAGE,
      _TAG_VALUE_NAME_WITHOUT_LANGUAGE])

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

  _ATTRIBUTE_NAME_TRANSLATION = {
      'com.apple.print.JobInfo.PMApplicationName': 'application',
      'com.apple.print.JobInfo.PMJobOwner': 'owner',
      'DestinationPrinterID': 'printer_id',
      'document-format': 'doc_type',
      'job-name': 'job_name',
      'job-originating-host-name': 'computer_name',
      'job-originating-user-name': 'user',
      'job-uuid': 'job_id',
      'printer-uri': 'uri'}

  def __init__(self):
    """Initializes a CUPS IPP file parser."""
    super(CupsIppParser, self).__init__()
    self._last_charset_attribute = 'ascii'

  def _GetStringValue(self, data_dict, name, default_value=None):
    """Retrieves a specific string value from the data dict.

    Args:
      data_dict (dict[str, list[str]]): values per name.
      name (str): name of the value to retrieve.
      default_value (Optional[object]): value to return if the name has no value
          set in data_dict.

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

  def _ParseAttribute(self, file_object):
    """Parses a CUPS IPP attribute from a file-like object.

    Args:
      file_object (dfvfs.FileIO): file-like object.

    Returns:
      tuple[str, object]: attribute name and value.

    Raises:
      ParseError: if the attribute cannot be parsed.
    """
    file_offset = file_object.tell()
    attribute_map = self._GetDataTypeMap('cups_ipp_attribute')

    try:
      attribute, _ = self._ReadStructureFromFileObject(
          file_object, file_offset, attribute_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse attribute with error: {0!s}'.format(exception))

    value = None
    if attribute.tag_value in self._INTEGER_TAG_VALUES:
      # TODO: correct file offset to point to the start of value_data.
      value = self._ParseIntegerValue(attribute.value_data, file_offset)

    elif attribute.tag_value == self._TAG_VALUE_BOOLEAN:
      value = self._ParseBooleanValue(attribute.value_data)

    elif attribute.tag_value == self._TAG_VALUE_DATE_TIME:
      # TODO: correct file offset to point to the start of value_data.
      value = self._ParseDateTimeValue(attribute.value_data, file_offset)

    elif attribute.tag_value in self._STRING_WITHOUT_LANGUAGE_VALUES:
      value = attribute.value_data.decode(self._last_charset_attribute)

    elif attribute.tag_value in self._ASCII_STRING_VALUES:
      value = attribute.value_data.decode('ascii')

      if attribute.tag_value == self._TAG_VALUE_CHARSET:
        self._last_charset_attribute = value

    else:
      value = attribute.value_data

    return attribute.name, value

  def _ParseAttributesGroup(self, file_object):
    """Parses a CUPS IPP attributes group from a file-like object.

    Args:
      file_object (dfvfs.FileIO): file-like object.

    Yields:
      tuple[str, object]: attribute name and value.

    Raises:
      ParseError: if the attributes group cannot be parsed.
    """
    tag_value_map = self._GetDataTypeMap('int8')
    tag_value = 0

    while tag_value != self._DELIMITER_TAG_END_OF_ATTRIBUTES:
      file_offset = file_object.tell()

      tag_value, _ = self._ReadStructureFromFileObject(
          file_object, file_offset, tag_value_map)

      if tag_value >= 0x10:
        file_object.seek(file_offset, os.SEEK_SET)

        yield self._ParseAttribute(file_object)

      elif (tag_value != self._DELIMITER_TAG_END_OF_ATTRIBUTES and
            tag_value not in self._DELIMITER_TAGS):
        raise errors.ParseError((
            'Unsupported attributes groups start tag value: '
            '0x{0:02x}.').format(tag_value))

  def _ParseBooleanValue(self, byte_stream):
    """Parses a boolean value.

    Args:
      byte_stream (bytes): byte stream.

    Returns:
      bool: boolean value.

    Raises:
      ParseError: when the boolean value cannot be parsed.
    """
    if byte_stream == b'\x00':
      return False

    if byte_stream == b'\x01':
      return True

    raise errors.ParseError('Unsupported boolean value.')

  def _ParseDateTimeValue(self, byte_stream, file_offset):
    """Parses a CUPS IPP RFC2579 date-time value from a byte stream.

    Args:
      byte_stream (bytes): byte stream.
      file_offset (int): offset of the attribute data relative to the start of
          the file-like object.

    Returns:
      dfdatetime.RFC2579DateTime: RFC2579 date-time stored in the value.

    Raises:
      ParseError: when the RFC2579 date-time value cannot be parsed.
    """
    datetime_value_map = self._GetDataTypeMap('cups_ipp_datetime_value')

    try:
      value = self._ReadStructureFromByteStream(
          byte_stream, file_offset, datetime_value_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse datetime value with error: {0!s}'.format(exception))

    direction_from_utc = chr(value.direction_from_utc)
    rfc2579_date_time_tuple = (
        value.year, value.month, value.day_of_month,
        value.hours, value.minutes, value.seconds, value.deciseconds,
        direction_from_utc, value.hours_from_utc, value.minutes_from_utc)
    return dfdatetime_rfc2579_date_time.RFC2579DateTime(
        rfc2579_date_time_tuple=rfc2579_date_time_tuple)

  def _ParseIntegerValue(self, byte_stream, file_offset):
    """Parses an integer value.

    Args:
      byte_stream (bytes): byte stream.
      file_offset (int): offset of the attribute data relative to the start of
          the file-like object.

    Returns:
      int: integer value.

    Raises:
      ParseError: when the integer value cannot be parsed.
    """
    data_type_map = self._GetDataTypeMap('int32be')

    try:
      return self._ReadStructureFromByteStream(
          byte_stream, file_offset, data_type_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse integer value with error: {0!s}'.format(exception))

  def _ParseHeader(self, parser_mediator, file_object):
    """Parses a CUPS IPP header from a file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the header cannot be parsed.
    """
    header_map = self._GetDataTypeMap('cups_ipp_header')

    try:
      header, _ = self._ReadStructureFromFileObject(file_object, 0, header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser(
          '[{0:s}] Unable to parse header with error: {1!s}'.format(
              self.NAME, exception))

    format_version = '{0:d}.{1:d}'.format(
        header.major_version, header.minor_version)
    if format_version not in self._SUPPORTED_FORMAT_VERSIONS:
      raise errors.WrongParser(
          '[{0:s}] Unsupported format version {1:s}.'.format(
              self.NAME, format_version))

    if header.operation_identifier != 5:
      # TODO: generate ExtractionWarning instead of printing debug output.
      display_name = parser_mediator.GetDisplayName()
      logger.debug((
          '[{0:s}] Non-standard operation identifier: 0x{1:08x} in file header '
          'of: {2:s}.').format(
              self.NAME, header.operation_identifier, display_name))

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a CUPS IPP file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    self._last_charset_attribute = 'ascii'

    self._ParseHeader(parser_mediator, file_object)

    data_dict = {}
    time_dict = {}
    is_first_attribute_group = True

    try:
      for name, value in self._ParseAttributesGroup(file_object):
        name = self._ATTRIBUTE_NAME_TRANSLATION.get(name, name)

        if name in self._DATE_TIME_VALUE_NAMES:
          time_dict.setdefault(name, []).append(value)
        else:
          data_dict.setdefault(name, []).append(value)

        is_first_attribute_group = False

    except (ValueError, errors.ParseError) as exception:
      error_message = (
          'unable to parse attribute group with error: {0!s}').format(exception)
      if is_first_attribute_group:
        raise errors.WrongParser(error_message)

      parser_mediator.ProduceExtractionWarning(error_message)
      return

    event_data = CupsIppEventData()
    event_data.application = self._GetStringValue(data_dict, 'application')
    event_data.computer_name = self._GetStringValue(data_dict, 'computer_name')
    event_data.copies = data_dict.get('copies', [0])[0]
    event_data.doc_type = self._GetStringValue(data_dict, 'doc_type')
    event_data.job_id = self._GetStringValue(data_dict, 'job_id')
    event_data.job_name = self._GetStringValue(data_dict, 'job_name')
    event_data.user = self._GetStringValue(data_dict, 'user')
    event_data.owner = self._GetStringValue(data_dict, 'owner')
    event_data.printer_id = self._GetStringValue(data_dict, 'printer_id')
    event_data.uri = self._GetStringValue(data_dict, 'uri')

    for name, usage in self._DATE_TIME_VALUES.items():
      for date_time in time_dict.get(name, []):
        event = time_events.DateTimeValuesEvent(date_time, usage)
        parser_mediator.ProduceEventWithEventData(event, event_data)

    for name, usage in self._POSIX_TIME_VALUES.items():
      for time_value in time_dict.get(name, []):
        date_time = dfdatetime_posix_time.PosixTime(timestamp=time_value)
        event = time_events.DateTimeValuesEvent(date_time, usage)
        parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(CupsIppParser)
