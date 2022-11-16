# -*- coding: utf-8 -*-
"""Parser for Java Cache IDX files."""

# TODO:
#  * 6.02 files did not retain IP addresses. However, the
#    deploy_resource_codebase header field may contain the host IP.
#    This needs to be researched further, as that field may not always
#    be present. 6.02 files will currently return 'Unknown'.

import os

from dfdatetime import java_time as dfdatetime_java_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class JavaIDXEventData(events.EventData):
  """Java IDX cache file event data.

  Attributes:
    downloaded_time (dfdatetime.DateTimeValues): date and time the content
        was downloaded.
    expiration_time (dfdatetime.DateTimeValues): date and time the cached
        download expires.
    idx_version (str): format version of IDX file.
    ip_address (str): IP address of the host in the URL.
    modification_time (dfdatetime.DateTimeValues): date and time the cached
        download expires.
    url (str): URL of the downloaded file.
  """

  DATA_TYPE = 'java:download:idx'

  def __init__(self):
    """Initializes event data."""
    super(JavaIDXEventData, self).__init__(data_type=self.DATA_TYPE)
    self.downloaded_time = None
    self.expiration_time = None
    self.idx_version = None
    self.ip_address = None
    self.modification_time = None
    self.url = None


class JavaIDXParser(interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
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

  NAME = 'java_idx'
  DATA_FORMAT = 'Java WebStart Cache IDX file'

  _INITIAL_FILE_OFFSET = None

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'java_idx.yaml')

  _SUPPORTED_FORMAT_VERSIONS = (602, 603, 604, 605)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Java WebStart Cache IDX file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object to parse.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    file_header_map = self._GetDataTypeMap('java_idx_file_header')

    try:
      file_header, file_offset = self._ReadStructureFromFileObject(
          file_object, 0, file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser(
          'Unable to parse file header with error: {0!s}'.format(
              exception))

    if not file_header.format_version in self._SUPPORTED_FORMAT_VERSIONS:
      raise errors.WrongParser('Unsupported format version.')

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
      raise errors.WrongParser((
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
      raise errors.WrongParser((
          'Unable to parse section 2 (format version: {0:d}) with error: '
          '{1!s}').format(file_header.format_version, exception))

    file_offset += data_size

    if not section2.url:
      raise errors.WrongParser('URL not found in file.')

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

    if date_http_header:
      # A HTTP header date and time should be formatted according to RFC 1123.
      # The date "should" be in UTC or have associated time zone information
      # in the string itself. If that is not the case then there is no reliable
      # method for Plaso to determine the proper time zone, so the assumption
      # is that the date and time is in UTC.
      try:
        downloaded_time = dfdatetime_time_elements.TimeElements()
        downloaded_time.CopyFromStringRFC1123(date_http_header.value)
      except ValueError as exception:
        parser_mediator.ProduceExtractionWarning((
            'Unable to parse date HTTP header string: {0:s} with error: '
            '{1!s}').format(date_http_header.value, exception))

    event_data = JavaIDXEventData()
    event_data.downloaded_time = downloaded_time
    event_data.idx_version = file_header.format_version
    event_data.ip_address = getattr(section2, 'ip_address', None)
    event_data.modification_time = dfdatetime_java_time.JavaTime(
        timestamp=section1.modification_time)
    event_data.url = section2.url

    if section1.expiration_time:
      event_data.expiration_time = dfdatetime_java_time.JavaTime(
          timestamp=section1.expiration_time)

    parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(JavaIDXParser)
