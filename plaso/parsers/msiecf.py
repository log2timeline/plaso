# -*- coding: utf-8 -*-
"""Parser for Microsoft Internet Explorer (MSIE) Cache Files (CF)."""

import pymsiecf

from dfdatetime import fat_date_time as dfdatetime_fat_date_time
from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class MSIECFLeakEventData(events.EventData):
  """MSIECF leak event data.

  Attributes:
    cached_filename (str): name of the cached file.
    cached_file_size (int): size of the cached file.
    cache_directory_index (int): index of the cache directory.
    cache_directory_name (str): name of the cache directory.
    offset (int): offset of the MSIECF item relative to the start of the file,
        from which the event data was extracted.
    recovered (bool): True if the item was recovered.
  """

  DATA_TYPE = 'msiecf:leak'

  def __init__(self):
    """Initializes event data."""
    super(MSIECFLeakEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cached_filename = None
    self.cached_file_size = None
    self.cache_directory_index = None
    self.cache_directory_name = None
    self.offset = None
    self.recovered = None


class MSIECFRedirectedEventData(events.EventData):
  """MSIECF redirected event data.

  Attributes:
    offset (int): offset of the MSIECF item relative to the start of the file,
        from which the event data was extracted.
    recovered (bool): True if the item was recovered.
    url (str): location URL.
  """

  DATA_TYPE = 'msiecf:redirected'

  def __init__(self):
    """Initializes event data."""
    super(MSIECFRedirectedEventData, self).__init__(data_type=self.DATA_TYPE)
    self.offset = None
    self.recovered = None
    self.url = None


class MSIECFURLEventData(events.EventData):
  """MSIECF URL event data.

  Attributes:
    access_time (dfdatetime.DateTimeValues): date and time the MSIECF item was
        last accessed.
    cached_filename (str): name of the cached file.
    cached_file_size (int): size of the cached file.
    cache_directory_index (int): index of the cache directory.
    cache_directory_name (str): name of the cache directory.
    creation_time (dfdatetime.DateTimeValues): date and time the MSIECF item
        was created.
    expiration_time (dfdatetime.DateTimeValues): date and time the MSIECF item
        expires.
    http_headers (str): HTTP headers.
    modification_time (dfdatetime.DateTimeValues): date and time the MSIECF
        item was last modified.
    last_visited_time (dfdatetime.DateTimeValues): date and time the MSIECF
        item was last visited.
    number_of_hits (int): number of hits.
    offset (int): offset of the MSIECF item relative to the start of the file,
        from which the event data was extracted.
    primary_time (dfdatetime.DateTimeValues): unspecified primary date and time
        of the MSIECF item.
    recovered (bool): True if the item was recovered.
    secondary_time (dfdatetime.DateTimeValues): unspecified secondary date and
        time of the MSIECF item.
    synchronization_time (dfdatetime.DateTimeValues): synchronization date
        and time.
    url (str): location URL.
  """

  DATA_TYPE = 'msiecf:url'

  def __init__(self):
    """Initializes event data."""
    super(MSIECFURLEventData, self).__init__(data_type=self.DATA_TYPE)
    self.access_time = None
    self.creation_time = None
    self.cached_filename = None
    self.cached_file_size = None
    self.cache_directory_index = None
    self.cache_directory_name = None
    self.creation_time = None
    self.expiration_time = None
    self.http_headers = None
    self.modification_time = None
    self.last_visited_time = None
    self.number_of_hits = None
    self.offset = None
    self.primary_time = None
    self.recovered = None
    self.secondary_time = None
    self.synchronization_time = None
    self.url = None


class MSIECFParser(interface.FileObjectParser):
  """Parses MSIE Cache Files (MSIECF)."""

  NAME = 'msiecf'
  DATA_FORMAT = (
      'Microsoft Internet Explorer (MSIE) 4 - 9 cache (index.dat) file')

  def _ParseLeak(
      self, parser_mediator, cache_directories, msiecf_item, recovered=False):
    """Extract data from a MSIE Cache Files (MSIECF) leak item.

    Every item is stored as an event object, one for each timestamp.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      cache_directories (list[str]): cache directory names.
      msiecf_item (pymsiecf.leak): MSIECF leak item.
      recovered (Optional[bool]): True if the item was recovered.
    """
    # TODO: add support for possible last cache synchronization date and time.

    event_data = MSIECFLeakEventData()
    event_data.cached_filename = msiecf_item.filename
    event_data.cached_file_size = msiecf_item.cached_file_size
    event_data.cache_directory_index = msiecf_item.cache_directory_index
    event_data.offset = msiecf_item.offset
    event_data.recovered = recovered

    if (event_data.cache_directory_index >= 0 and
        event_data.cache_directory_index < len(cache_directories)):
      event_data.cache_directory_name = (
          cache_directories[event_data.cache_directory_index])

    parser_mediator.ProduceEventData(event_data)

  def _ParseItems(self, parser_mediator, msiecf_file):
    """Parses a MSIE Cache File (MSIECF) items.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      msiecf_file (pymsiecf.file): MSIECF file.
    """
    format_version = msiecf_file.format_version

    decode_error = False
    cache_directories = []
    for cache_directory_name in msiecf_file.cache_directories:
      try:
        cache_directory_name = cache_directory_name.decode('ascii')
      except UnicodeDecodeError:
        decode_error = True
        cache_directory_name = cache_directory_name.decode(
            'ascii', errors='replace')

      cache_directories.append(cache_directory_name)

    if decode_error:
      parser_mediator.ProduceExtractionWarning((
          'unable to decode cache directory names. Characters that cannot '
          'be decoded will be replaced with "?" or "\\ufffd".'))

    for item_index in range(0, msiecf_file.number_of_items):
      try:
        msiecf_item = msiecf_file.get_item(item_index)
        if isinstance(msiecf_item, pymsiecf.leak):
          self._ParseLeak(parser_mediator, cache_directories, msiecf_item)

        elif isinstance(msiecf_item, pymsiecf.redirected):
          self._ParseRedirected(parser_mediator, msiecf_item)

        elif isinstance(msiecf_item, pymsiecf.url):
          self._ParseUrl(
              parser_mediator, format_version, cache_directories, msiecf_item)

      except IOError as exception:
        parser_mediator.ProduceExtractionWarning(
            'Unable to parse item: {0:d} with error: {1!s}'.format(
                item_index, exception))

    for item_index in range(0, msiecf_file.number_of_recovered_items):
      try:
        msiecf_item = msiecf_file.get_recovered_item(item_index)
        if isinstance(msiecf_item, pymsiecf.leak):
          self._ParseLeak(
              parser_mediator, cache_directories, msiecf_item, recovered=True)

        elif isinstance(msiecf_item, pymsiecf.redirected):
          self._ParseRedirected(parser_mediator, msiecf_item, recovered=True)

        elif isinstance(msiecf_item, pymsiecf.url):
          self._ParseUrl(
              parser_mediator, format_version, cache_directories, msiecf_item,
              recovered=True)

      except IOError as exception:
        parser_mediator.ProduceRecoveryWarning(
            'Unable to parse recovered item: {0:d} with error: {1!s}'.format(
                item_index, exception))

  def _ParseRedirected(
      self, parser_mediator, msiecf_item, recovered=False):
    """Extract data from a MSIE Cache Files (MSIECF) redirected item.

    Every item is stored as an event object, one for each timestamp.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      msiecf_item (pymsiecf.redirected): MSIECF redirected item.
      recovered (Optional[bool]): True if the item was recovered.
    """
    event_data = MSIECFRedirectedEventData()
    event_data.offset = msiecf_item.offset
    event_data.recovered = recovered
    event_data.url = msiecf_item.location

    parser_mediator.ProduceEventData(event_data)

  def _ParseUrl(
      self, parser_mediator, format_version, cache_directories, msiecf_item,
      recovered=False):
    """Extract data from a MSIE Cache Files (MSIECF) URL item.

    Every item is stored as an event object, one for each timestamp.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      format_version (str): MSIECF format version.
      cache_directories (list[str]): cache directory names.
      msiecf_item (pymsiecf.url): MSIECF URL item.
      recovered (Optional[bool]): True if the item was recovered.
    """
    # The secondary time can be stored in either UTC or local time this is
    # dependent on what the index.dat file is used for. Either the file path
    # or location string can be used to distinguish between the different types
    # of files.

    primary_timestamp = msiecf_item.get_primary_time_as_integer()
    secondary_timestamp = msiecf_item.get_secondary_time_as_integer()

    primary_date_time = None
    if primary_timestamp:
      primary_date_time = dfdatetime_filetime.Filetime(
          timestamp=primary_timestamp)

    secondary_date_time = None
    if secondary_timestamp:
      secondary_date_time = dfdatetime_filetime.Filetime(
          timestamp=secondary_timestamp)

      if msiecf_item.type in ('history-daily', 'history-weekly'):
        secondary_date_time.is_local_time = True

    http_headers = ''
    if msiecf_item.type and msiecf_item.data:
      if msiecf_item.type == 'cache':
        if msiecf_item.data[:4] == b'HTTP':
          # Make sure the HTTP headers are ASCII encoded.
          # TODO: determine correct encoding currently indications that
          # this could be the system narrow string code page.
          try:
            http_headers = msiecf_item.data[:-1].decode('ascii')
          except UnicodeDecodeError:
            warning_message = (
                'unable to decode HTTP headers of URL record at offset: '
                '0x{0:08x}. Characters that cannot be decoded will be '
                'replaced with "?" or "\\ufffd".').format(msiecf_item.offset)
            if recovered:
              parser_mediator.ProduceRecoveryWarning(warning_message)
            else:
              parser_mediator.ProduceExtractionWarning(warning_message)
            http_headers = msiecf_item.data[:-1].decode(
                'ascii', errors='replace')

      # TODO: parse data of other URL item type like history which requires
      # OLE VT parsing.

    event_data = MSIECFURLEventData()
    event_data.cached_filename = msiecf_item.filename
    event_data.cached_file_size = msiecf_item.cached_file_size
    event_data.cache_directory_index = msiecf_item.cache_directory_index
    event_data.http_headers = http_headers
    event_data.number_of_hits = msiecf_item.number_of_hits
    event_data.offset = msiecf_item.offset
    event_data.recovered = recovered
    event_data.url = msiecf_item.location

    if (event_data.cache_directory_index >= 0 and
        event_data.cache_directory_index < len(cache_directories)):
      event_data.cache_directory_name = (
          cache_directories[event_data.cache_directory_index])

    if msiecf_item.type in ('cache', 'cookie'):
      event_data.access_time = primary_date_time
      event_data.modification_time = secondary_date_time

    elif msiecf_item.type in ('history', 'history-daily'):
      event_data.last_visited_time = primary_date_time
      event_data.secondary_time = secondary_date_time

    elif msiecf_item.type == 'history-weekly':
      event_data.creation_time = primary_date_time
      event_data.last_visited_time = secondary_date_time

    else:
      event_data.primary_time = primary_date_time
      event_data.secondary_time = secondary_date_time

    expiration_timestamp = msiecf_item.get_expiration_time_as_integer()
    if expiration_timestamp:
      # The expiration time in MSIECF version 4.7 is stored as a FILETIME value
      # in version 5.2 it is stored as a FAT date time value.
      # Since the as_integer function returns the raw integer value we need to
      # apply the right conversion here.
      if format_version == '4.7':
        if expiration_timestamp == 0x7fffffffffffffff:
          expiration_date_time = dfdatetime_semantic_time.Never()
        else:
          expiration_date_time = dfdatetime_filetime.Filetime(
              timestamp=expiration_timestamp)
      else:
        if expiration_timestamp == 0xffffffff:
          expiration_date_time = dfdatetime_semantic_time.Never()
        else:
          expiration_date_time = dfdatetime_fat_date_time.FATDateTime(
              fat_date_time=expiration_timestamp)

      event_data.expiration_time = expiration_date_time

    last_checked_timestamp = msiecf_item.get_last_checked_time_as_integer()
    if last_checked_timestamp != 0:
      event_data.synchronization_time = dfdatetime_fat_date_time.FATDateTime(
          fat_date_time=last_checked_timestamp)

    parser_mediator.ProduceEventData(event_data)

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(
        b'Client\x20UrlCache\x20MMF\x20Ver\x20', offset=0)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a MSIE Cache File (MSIECF) file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.
    """
    code_page = parser_mediator.GetCodePage()

    msiecf_file = pymsiecf.file()
    msiecf_file.set_ascii_codepage(code_page)

    try:
      msiecf_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open file with error: {0!s}'.format(exception))
      return

    try:
      self._ParseItems(parser_mediator, msiecf_file)
    finally:
      msiecf_file.close()


manager.ParsersManager.RegisterParser(MSIECFParser)
