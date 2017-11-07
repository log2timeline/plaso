# -*- coding: utf-8 -*-
"""Parser for Microsoft Internet Explorer (MSIE) Cache Files (CF)."""

from __future__ import unicode_literals

import pymsiecf

from dfdatetime import fat_date_time as dfdatetime_fat_date_time
from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
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
    self.recovered = None


class MSIECFRedirectedEventData(events.EventData):
  """MSIECF redirected event data.

  Attributes:
    recovered (bool): True if the item was recovered.
    url (str): location URL.
  """

  DATA_TYPE = 'msiecf:redirected'

  def __init__(self):
    """Initializes event data."""
    super(MSIECFRedirectedEventData, self).__init__(data_type=self.DATA_TYPE)
    self.recovered = None
    self.url = None


class MSIECFURLEventData(events.EventData):
  """MSIECF URL event data.

  Attributes:
    cached_filename (str): name of the cached file.
    cached_file_size (int): size of the cached file.
    cache_directory_index (int): index of the cache directory.
    cache_directory_name (str): name of the cache directory.
    http_headers (str): HTTP headers.
    number_of_hits (int): number of hits.
    recovered (bool): True if the item was recovered.
    url (str): location URL.
  """

  DATA_TYPE = 'msiecf:url'

  def __init__(self):
    """Initializes event data."""
    super(MSIECFURLEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cached_filename = None
    self.cached_file_size = None
    self.cache_directory_index = None
    self.cache_directory_name = None
    self.http_headers = None
    self.number_of_hits = None
    self.offset = None
    self.recovered = None
    self.url = None


class MSIECFParser(interface.FileObjectParser):
  """Parses MSIE Cache Files (MSIECF)."""

  NAME = 'msiecf'
  DESCRIPTION = 'Parser for MSIE Cache Files (MSIECF) also known as index.dat.'

  def _ParseLeak(
      self, parser_mediator, cache_directories, msiecf_item, recovered=False):
    """Extract data from a MSIE Cache Files (MSIECF) leak item.

    Every item is stored as an event object, one for each timestamp.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      cache_directories (list[str]): cache directory names.
      msiecf_item (pymsiecf.leak): MSIECF leak item.
      recovered (Optional[bool]): True if the item was recovered.
    """
    # TODO: add support for possible last cache synchronization date and time.
    date_time = dfdatetime_semantic_time.SemanticTime('Not set')

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

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseItems(self, parser_mediator, msiecf_file):
    """Parses a MSIE Cache File (MSIECF) items.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      msiecf_file (pymsiecf.file): MSIECF file.
    """
    format_version = msiecf_file.format_version
    cache_directories = []
    for cache_directory_name in iter(msiecf_file.cache_directories):
      cache_directories.append(cache_directory_name)

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
        parser_mediator.ProduceExtractionError(
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
        parser_mediator.ProduceExtractionError(
            'Unable to parse recovered item: {0:d} with error: {1!s}'.format(
                item_index, exception))

  def _ParseRedirected(
      self, parser_mediator, msiecf_item, recovered=False):
    """Extract data from a MSIE Cache Files (MSIECF) redirected item.

    Every item is stored as an event object, one for each timestamp.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      msiecf_item (pymsiecf.redirected): MSIECF redirected item.
      recovered (Optional[bool]): True if the item was recovered.
    """
    date_time = dfdatetime_semantic_time.SemanticTime('Not set')

    event_data = MSIECFRedirectedEventData()
    event_data.offset = msiecf_item.offset
    event_data.recovered = recovered
    event_data.url = msiecf_item.location

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseUrl(
      self, parser_mediator, format_version, cache_directories, msiecf_item,
      recovered=False):
    """Extract data from a MSIE Cache Files (MSIECF) URL item.

    Every item is stored as an event object, one for each timestamp.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      format_version (str): MSIECF format version.
      cache_directories (list[str]): cache directory names.
      msiecf_item (pymsiecf.url): MSIECF URL item.
      recovered (Optional[bool]): True if the item was recovered.
    """
    # The secondary time can be stored in either UTC or local time
    # this is dependent on what the index.dat file is used for.
    # Either the file path or location string can be used to distinguish
    # between the different type of files.
    timestamp = msiecf_item.get_primary_time_as_integer()
    if not timestamp:
      primary_date_time = dfdatetime_semantic_time.SemanticTime('Not set')
    else:
      primary_date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
    primary_date_time_description = 'Primary Time'

    timestamp = msiecf_item.get_secondary_time_as_integer()
    secondary_date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
    secondary_date_time_description = 'Secondary Time'

    if msiecf_item.type:
      if msiecf_item.type == 'cache':
        primary_date_time_description = definitions.TIME_DESCRIPTION_LAST_ACCESS
        secondary_date_time_description = (
            definitions.TIME_DESCRIPTION_MODIFICATION)

      elif msiecf_item.type == 'cookie':
        primary_date_time_description = definitions.TIME_DESCRIPTION_LAST_ACCESS
        secondary_date_time_description = (
            definitions.TIME_DESCRIPTION_MODIFICATION)

      elif msiecf_item.type == 'history':
        primary_date_time_description = (
            definitions.TIME_DESCRIPTION_LAST_VISITED)
        secondary_date_time_description = (
            definitions.TIME_DESCRIPTION_LAST_VISITED)

      elif msiecf_item.type == 'history-daily':
        primary_date_time_description = (
            definitions.TIME_DESCRIPTION_LAST_VISITED)
        secondary_date_time_description = (
            definitions.TIME_DESCRIPTION_LAST_VISITED)
        # The secondary_date_time is in localtime normalize it to be in UTC.
        secondary_date_time.is_local_time = True

      elif msiecf_item.type == 'history-weekly':
        primary_date_time_description = definitions.TIME_DESCRIPTION_CREATION
        secondary_date_time_description = (
            definitions.TIME_DESCRIPTION_LAST_VISITED)
        # The secondary_date_time is in localtime normalize it to be in UTC.
        secondary_date_time.is_local_time = True

    http_headers = ''
    if msiecf_item.type and msiecf_item.data:
      if msiecf_item.type == 'cache':
        if msiecf_item.data[:4] == b'HTTP':
          # Make sure the HTTP headers are ASCII encoded.
          # TODO: determine correct encoding currently indications that
          # this could be the system narrow string codepage.
          try:
            http_headers = msiecf_item.data[:-1].decode('ascii')
          except UnicodeDecodeError:
            parser_mediator.ProduceExtractionError((
                'unable to decode HTTP headers of URL record at offset: '
                '0x{0:08x}. Characters that cannot be decoded will be '
                'replaced with "?" or "\\ufffd".').format(msiecf_item.offset))
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

    event = time_events.DateTimeValuesEvent(
        primary_date_time, primary_date_time_description)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    if secondary_date_time.timestamp != 0:
      event = time_events.DateTimeValuesEvent(
          secondary_date_time, secondary_date_time_description,
          time_zone=parser_mediator.timezone)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    expiration_timestamp = msiecf_item.get_expiration_time_as_integer()
    if expiration_timestamp != 0:
      # The expiration time in MSIECF version 4.7 is stored as a FILETIME value
      # in version 5.2 it is stored as a FAT date time value.
      # Since the as_integer function returns the raw integer value we need to
      # apply the right conversion here.
      if format_version == '4.7':
        if expiration_timestamp == 0x7fffffffffffffff:
          expiration_date_time = dfdatetime_semantic_time.SemanticTime('Never')
        else:
          expiration_date_time = dfdatetime_filetime.Filetime(
              timestamp=expiration_timestamp)
      else:
        if expiration_timestamp == 0xffffffff:
          expiration_date_time = dfdatetime_semantic_time.SemanticTime('Never')
        else:
          expiration_date_time = dfdatetime_fat_date_time.FATDateTime(
              fat_date_time=expiration_timestamp)

      event = time_events.DateTimeValuesEvent(
          expiration_date_time, definitions.TIME_DESCRIPTION_EXPIRATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    last_checked_timestamp = msiecf_item.get_last_checked_time_as_integer()
    if last_checked_timestamp != 0:
      last_checked_date_time = dfdatetime_fat_date_time.FATDateTime(
          fat_date_time=last_checked_timestamp)

      event = time_events.DateTimeValuesEvent(
          last_checked_date_time, definitions.TIME_DESCRIPTION_LAST_CHECKED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

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

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a MSIE Cache File (MSIECF) file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    msiecf_file = pymsiecf.file()
    msiecf_file.set_ascii_codepage(parser_mediator.codepage)

    try:
      msiecf_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionError(
          'unable to open file with error: {0!s}'.format(exception))
      return

    try:
      self._ParseItems(parser_mediator, msiecf_file)
    finally:
      msiecf_file.close()


manager.ParsersManager.RegisterParser(MSIECFParser)
