# -*- coding: utf-8 -*-
"""Parser for Safari Binary Cookie files."""

import construct

from dfdatetime import cocoa_time as dfdatetime_cocoa_time
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import specification
# Need to register cookie plugins.
from plaso.parsers import cookie_plugins  # pylint: disable=unused-import
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers.cookie_plugins import manager as cookie_plugins_manager


class SafariBinaryCookieEventData(events.EventData):
  """Safari binary cookie event data.

  Attributes:
    cookie_name (str): cookie name.
    cookie_value (str): cookie value.
    flags (int): cookie flags.
    path (str): path of the cookie.
    url (str): URL where this cookie is valid.
  """

  DATA_TYPE = u'safari:cookie:entry'

  def __init__(self):
    """Initializes event data."""
    super(SafariBinaryCookieEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cookie_name = None
    self.cookie_value = None
    self.flags = None
    self.path = None
    self.url = None


class BinaryCookieParser(interface.FileObjectParser):
  """Parser for Safari Binary Cookie files."""

  NAME = u'binary_cookies'
  DESCRIPTION = u'Parser for Safari Binary Cookie files.'

  _FILE_HEADER = construct.Struct(
      u'file_header',
      construct.Bytes(u'signature', 4),
      construct.UBInt32(u'number_of_pages'),
      construct.Array(
          lambda ctx: ctx.number_of_pages,
          construct.UBInt32(u'page_sizes')))

  _COOKIE_RECORD = construct.Struct(
      u'cookie_record',
      construct.ULInt32(u'size'),
      construct.Bytes(u'unknown_1', 4),
      construct.ULInt32(u'flags'),
      construct.Bytes(u'unknown_2', 4),
      construct.ULInt32(u'url_offset'),
      construct.ULInt32(u'name_offset'),
      construct.ULInt32(u'path_offset'),
      construct.ULInt32(u'value_offset'),
      construct.Bytes(u'end_of_cookie', 8),
      construct.LFloat64(u'expiration_date'),
      construct.LFloat64(u'creation_date'))

  _PAGE_HEADER = construct.Struct(
      u'page_header',
      construct.Bytes(u'header', 4),
      construct.ULInt32(u'number_of_records'),
      construct.Array(
          lambda ctx: ctx.number_of_records,
          construct.ULInt32(u'offsets')))

  def __init__(self):
    """Initializes a parser object."""
    super(BinaryCookieParser, self).__init__()
    self._cookie_plugins = (
        cookie_plugins_manager.CookiePluginsManager.GetPlugins())

  def _ParseCookieRecord(self, parser_mediator, page_data, page_offset):
    """Parses a cookie record

    Args:
      parser_mediator (ParserMediator): parser mediator.
      page_data (bytes): page data.
      page_offset (int): offset of the cookie record relative to the start
          of the page.
    """
    try:
      cookie = self._COOKIE_RECORD.parse(page_data[page_offset:])
    except construct.FieldError:
      message = u'Unable to read cookie record at offset: {0:d}'.format(
          page_offset)
      parser_mediator.ProduceExtractionError(message)
      return

    # The offset is determined by the range between the start of the current
    # offset until the start of the next offset. Thus we need to determine
    # the proper ordering of the offsets, since they are not always in the
    # same ordering.
    offset_dict = {
        cookie.url_offset: u'url', cookie.name_offset: u'name',
        cookie.value_offset: u'value', cookie.path_offset: u'path'}

    offsets = sorted(offset_dict.keys())
    offsets.append(cookie.size + page_offset)

    # TODO: Find a better approach to parsing the data than this.
    data_dict = {}
    for current_offset in range(0, len(offsets) - 1):
      # Get the current offset and the offset for the next entry.
      start, end = offsets[current_offset:current_offset+2]
      value = offset_dict.get(offsets[current_offset])
      # Read the data.
      data_all = page_data[start + page_offset:end + page_offset]
      data, _, _ = data_all.partition(b'\x00')
      data_dict[value] = data

    event_data = SafariBinaryCookieEventData()
    event_data.cookie_name = data_dict.get(u'name')
    event_data.cookie_value = data_dict.get(u'value')
    event_data.flags = cookie.flags
    event_data.path = data_dict.get(u'path')
    event_data.url = data_dict.get(u'url')

    if cookie.creation_date:
      date_time = dfdatetime_cocoa_time.CocoaTime(
          timestamp=cookie.creation_date)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    if cookie.expiration_date:
      date_time = dfdatetime_cocoa_time.CocoaTime(
          timestamp=cookie.expiration_date)
    else:
      date_time = dfdatetime_semantic_time.SemanticTime(u'Not set')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_EXPIRATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    for plugin in self._cookie_plugins:
      if parser_mediator.abort:
        break

      if event_data.cookie_name != plugin.COOKIE_NAME:
        continue

      try:
        plugin.UpdateChainAndProcess(
            parser_mediator, cookie_name=event_data.cookie_name,
            cookie_data=event_data.cookie_value, url=event_data.url)

      except Exception as exception:  # pylint: disable=broad-except
        parser_mediator.ProduceExtractionError(
            u'plugin: {0:s} unable to parse cookie with error: {1:s}'.format(
                plugin.NAME, exception))

  def _ParsePage(self, parser_mediator, page_number, page_data):
    """Parses a page.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      page_number (int): page number.
      page_data (bytes): page data.
    """
    try:
      page_header = self._PAGE_HEADER.parse(page_data)
    except construct.FieldError:
      # TODO: add offset
      parser_mediator.ProduceExtractionError(
          u'unable to read header of page: {0:d} at offset: 0x{1:08x}'.format(
              page_number, 0))
      return

    for page_offset in page_header.offsets:
      if parser_mediator.abort:
        break

      self._ParseCookieRecord(parser_mediator, page_data, page_offset)

    # TODO: check footer.

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification for parser selection.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'cook\x00', offset=0)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Safari binary cookie file-like object.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfs.FileIO): file-like object to be parsed.

    Raises:
      UnableToParseFile: when the file cannot be parsed, this will signal
          the event extractor to apply other parsers.
    """
    try:
      file_header = self._FILE_HEADER.parse_stream(file_object)
    except (IOError, construct.ArrayError, construct.FieldError) as exception:
      parser_mediator.ProduceExtractionError(
          u'unable to read file header with error: {0:s}.'.format(exception))
      raise errors.UnableToParseFile()

    if file_header.signature != b'cook':
      parser_mediator.ProduceExtractionError(u'unsupported file signature.')
      raise errors.UnableToParseFile()

    for index, page_size in enumerate(file_header.page_sizes):
      if parser_mediator.abort:
        break

      page_data = file_object.read(page_size)
      if len(page_data) != page_size:
        parser_mediator.ProduceExtractionError(
            u'unable to read page: {0:d}'.format(index))
        break

      self._ParsePage(parser_mediator, index, page_data)


manager.ParsersManager.RegisterParser(BinaryCookieParser)
