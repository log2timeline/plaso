# -*- coding: utf-8 -*-
"""Parser for Safari Binary Cookie files."""

import os

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.containers import events
from plaso.lib import cookie_plugins_helper
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class SafariBinaryCookieEventData(events.EventData):
  """Safari binary cookie event data.

  Attributes:
    cookie_name (str): cookie name.
    cookie_value (str): cookie value.
    creation_time (dfdatetime.DateTimeValues): date and time the cookie
        was created.
    expiration_time (dfdatetime.DateTimeValues): date and time the cookie
        expires.
    flags (int): cookie flags.
    path (str): path of the cookie.
    url (str): URL where this cookie is valid.
  """

  DATA_TYPE = 'safari:cookie:entry'

  def __init__(self):
    """Initializes event data."""
    super(SafariBinaryCookieEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cookie_name = None
    self.cookie_value = None
    self.creation_time = None
    self.expiration_time = None
    self.flags = None
    self.path = None
    self.url = None


class BinaryCookieParser(
    interface.FileObjectParser, cookie_plugins_helper.CookiePluginsHelper,
    dtfabric_helper.DtFabricHelper):
  """Parser for Safari Binary Cookie files."""

  NAME = 'binary_cookies'
  DATA_FORMAT = 'Safari Binary Cookie file'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'safari_cookies.yaml')

  def _ParseCString(self, page_data, string_offset):
    """Parses a C string from the page data.

    Args:
      page_data (bytes): page data.
      string_offset (int): offset of the string relative to the start
          of the page.

    Returns:
      str: string.

    Raises:
      ParseError: when the string cannot be parsed.
    """
    cstring_map = self._GetDataTypeMap('cstring')

    try:
      value_string = self._ReadStructureFromByteStream(
          page_data[string_offset:], string_offset, cstring_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to map string data at offset: 0x{0:08x} with error: '
          '{1!s}').format(string_offset, exception))

    return value_string.rstrip('\x00')

  def _ParsePage(self, parser_mediator, file_offset, page_data):
    """Parses a page.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_offset (int): offset of the data relative from the start of
          the file-like object.
      page_data (bytes): page data.

    Raises:
      ParseError: when the page cannot be parsed.
    """
    page_header_map = self._GetDataTypeMap('binarycookies_page_header')

    try:
      page_header = self._ReadStructureFromByteStream(
          page_data, file_offset, page_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to map page header data at offset: 0x{0:08x} with error: '
          '{1!s}').format(file_offset, exception))

    for record_offset in page_header.offsets:
      if parser_mediator.abort:
        break

      self._ParseRecord(parser_mediator, page_data, record_offset)

  def _ParseRecord(self, parser_mediator, page_data, record_offset):
    """Parses a record from the page data.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      page_data (bytes): page data.
      record_offset (int): offset of the record relative to the start
          of the page.

    Raises:
      ParseError: when the record cannot be parsed.
    """
    record_header_map = self._GetDataTypeMap('binarycookies_record_header')

    try:
      record_header = self._ReadStructureFromByteStream(
          page_data[record_offset:], record_offset, record_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to map record header data at offset: 0x{0:08x} with error: '
          '{1!s}').format(record_offset, exception))

    event_data = SafariBinaryCookieEventData()
    event_data.flags = record_header.flags

    if record_header.url_offset:
      data_offset = record_offset + record_header.url_offset
      event_data.url = self._ParseCString(page_data, data_offset)

    if record_header.name_offset:
      data_offset = record_offset + record_header.name_offset
      event_data.cookie_name = self._ParseCString(page_data, data_offset)

    if record_header.path_offset:
      data_offset = record_offset + record_header.path_offset
      event_data.path = self._ParseCString(page_data, data_offset)

    if record_header.value_offset:
      data_offset = record_offset + record_header.value_offset
      event_data.cookie_value = self._ParseCString(page_data, data_offset)

    if record_header.creation_time:
      event_data.creation_time = dfdatetime_cocoa_time.CocoaTime(
          timestamp=record_header.creation_time)

    if record_header.expiration_time:
      event_data.expiration_time = dfdatetime_cocoa_time.CocoaTime(
          timestamp=record_header.expiration_time)

    parser_mediator.ProduceEventData(event_data)

    self._ParseCookie(
        parser_mediator, event_data.cookie_name, event_data.cookie_value,
        event_data.cookie_name)

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification for parser selection.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'cook\x00', offset=0)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Safari binary cookie file-like object.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfs.FileIO): file-like object to be parsed.

    Raises:
      ParseError: when the page sizes array cannot be parsed.
      WrongParser: when the file cannot be parsed, this will signal
          the event extractor to apply other parsers.
    """
    file_header_map = self._GetDataTypeMap('binarycookies_file_header')

    try:
      file_header, file_header_data_size = self._ReadStructureFromFileObject(
          file_object, 0, file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser(
          'Unable to read file header with error: {0!s}.'.format(exception))

    file_offset = file_header_data_size

    # TODO: move page sizes array into file header, this will require dtFabric
    # to compare signature as part of data map.
    page_sizes_data_size = file_header.number_of_pages * 4

    page_sizes_data = file_object.read(page_sizes_data_size)

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'binarycookies_file_header': file_header})

    page_sizes_map = self._GetDataTypeMap('binarycookies_page_sizes')

    try:
      page_sizes_array = self._ReadStructureFromByteStream(
          page_sizes_data, file_offset, page_sizes_map, context=context)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to map page sizes data at offset: 0x{0:08x} with error: '
          '{1!s}').format(file_offset, exception))

    file_offset += page_sizes_data_size

    for page_number, page_size in enumerate(page_sizes_array):
      if parser_mediator.abort:
        break

      page_data = file_object.read(page_size)
      if len(page_data) != page_size:
        parser_mediator.ProduceExtractionWarning(
            'unable to read page: {0:d}'.format(page_number))
        break

      self._ParsePage(parser_mediator, file_offset, page_data)

      file_offset += page_size

    # TODO: check file footer.


manager.ParsersManager.RegisterParser(BinaryCookieParser)
