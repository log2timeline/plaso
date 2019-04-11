# -*- coding: utf-8 -*-
"""Parser for Java Cache IDX files."""

from __future__ import unicode_literals

# TODO:
#  * 6.02 files did not retain IP addresses. However, the
#    deploy_resource_codebase header field may contain the host IP.
#    This needs to be researched further, as that field may not always
#    be present. 6.02 files will currently return 'Unknown'.

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import dtfabric_parser
from plaso.parsers import manager


class JavaIDXEventData(events.EventData):
  """Java IDX cache file event data.

  Attributes:
    idx_version (str): format version of IDX file.
    ip_address (str): IP address of the host in the URL.
    url (str): URL of the downloaded file.
  """

  DATA_TYPE = 'java:download:idx'

  def __init__(self):
    """Initializes event data."""
    super(JavaIDXEventData, self).__init__(data_type=self.DATA_TYPE)
    self.idx_version = None
    self.ip_address = None
    self.url = None


class JavaIDXParser(dtfabric_parser.DtFabricBaseParser):
  """Parser for Java WebStart Cache IDX files.

  There are five structures defined. 6.02 files had one generic section
  that retained all data. From 6.03, the file went to a multi-section
  format where later sections were optional and had variable-lengths.
  6.03, 6.04, and 6.05 files all have their main data section (#2)
  begin at offset 128. The short structure is because 6.05 files
  deviate after the 8th byte. So, grab the first 8 bytes to ensure it's
  valid, get the file version, then continue on with the correct
  structures.
  """

  _INITIAL_FILE_OFFSET = None

  NAME = 'java_idx'
  DESCRIPTION = 'Parser for Java WebStart Cache IDX files.'

  _DEFINITION_FILE = 'java_idx.yaml'

  _SUPPORTED_FORMAT_VERSIONS = (602, 603, 604, 605)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Java WebStart Cache IDX file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dvfvs.FileIO): a file-like object to parse.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_header_map = self._GetDataTypeMap('java_idx_file_header')

    try:
      file_header, file_offset = self._ReadStructureFromFileObject(
          file_object, 0, file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.UnableToParseFile(
          'Unable to parse file header with error: {0!s}'.format(
              exception))

    if not file_header.format_version in self._SUPPORTED_FORMAT_VERSIONS:
      raise errors.UnableToParseFile('Unsupported format version.')

    if file_header.format_version == 602:
      section1_map = self._GetDataTypeMap('java_idx_602_section1')
    elif file_header.format_version in (603, 604):
      section1_map = self._GetDataTypeMap('java_idx_603_section1')
    elif file_header.format_version == 605:
      section1_map = self._GetDataTypeMap('java_idx_605_section1')

    try:
      section1, data_size = self._ReadStructureFromFileObject(
          file_object, file_offset, section1_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.UnableToParseFile((
          'Unable to parse section 1 (format version: {0:d}) with error: '
          '{1!s}').format(file_header.format_version, exception))

    file_offset += data_size

    if file_header.format_version == 602:
      section2_map = self._GetDataTypeMap('java_idx_602_section2')
    elif file_header.format_version in (603, 604, 605):
      file_offset = 128
      section2_map = self._GetDataTypeMap('java_idx_603_section2')

    try:
      section2, data_size = self._ReadStructureFromFileObject(
          file_object, file_offset, section2_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.UnableToParseFile((
          'Unable to parse section 2 (format version: {0:d}) with error: '
          '{1!s}').format(file_header.format_version, exception))

    file_offset += data_size

    if not section2.url:
      raise errors.UnableToParseFile('URL not found in file.')

    date_http_header = None
    for _ in range(section2.number_of_http_headers):
      http_header_map = self._GetDataTypeMap('java_idx_http_header')
      try:
        http_header, data_size = self._ReadStructureFromFileObject(
            file_object, file_offset, http_header_map)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning(
            'Unable to parse HTTP header value at offset: 0x{0:08x}'.format(
                file_offset))
        break

      file_offset += data_size

      if http_header.name == 'date':
        date_http_header = http_header
        break

    event_data = JavaIDXEventData()
    event_data.idx_version = file_header.format_version
    event_data.ip_address = getattr(section2, 'ip_address', None)
    event_data.url = section2.url

    date_time = dfdatetime_java_time.JavaTime(
        timestamp=section1.modification_time)
    # TODO: Move the timestamp description into definitions.
    event = time_events.DateTimeValuesEvent(date_time, 'File Hosted Date')
    parser_mediator.ProduceEventWithEventData(event, event_data)

    if section1.expiration_time:
      date_time = dfdatetime_java_time.JavaTime(
          timestamp=section1.expiration_time)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_EXPIRATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    if date_http_header:
      # A HTTP header date and string "should" be in UTC or have an associated
      # time zone information in the string itself. If that is not the case
      # then there is no reliable method for plaso to determine the proper
      # time zone, so the assumption is that it is UTC.
      try:
        download_date = timelib.Timestamp.FromTimeString(
            date_http_header.value, gmt_as_timezone=False)
      except errors.TimestampError:
        parser_mediator.ProduceExtractionWarning(
            'Unable to parse date HTTP header value: {0:s}'.format(
                date_http_header.value))

      if download_date:
        event = time_events.TimestampEvent(
            download_date, definitions.TIME_DESCRIPTION_FILE_DOWNLOADED)
        parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(JavaIDXParser)
