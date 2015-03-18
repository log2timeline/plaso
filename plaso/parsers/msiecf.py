# -*- coding: utf-8 -*-
"""Parser for Microsoft Internet Explorer (MSIE) Cache Files (CF)."""

import pymsiecf

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


if pymsiecf.get_version() < '20150314':
  raise ImportWarning(u'MsiecfParser requires at least pymsiecf 20150314.')


class MsiecfLeakEvent(time_events.TimestampEvent):
  """Convenience class for an MSIECF leak event."""

  DATA_TYPE = 'msiecf:leak'

  def __init__(
      self, timestamp, timestamp_description, cache_directories, msiecf_item,
      recovered=False):
    """Initializes the event.

    Args:
      timestamp: The timestamp value.
      timestamp_description: The usage string describing the timestamp.
      cache_directories: A list of cache directory names.
      msiecf_item: The MSIECF item (pymsiecf.leak).
      recovered: Boolean value to indicate the item was recovered, False
                 by default.
    """
    super(MsiecfLeakEvent, self).__init__(timestamp, timestamp_description)

    self.recovered = recovered
    self.offset = msiecf_item.offset

    self.cached_filename = msiecf_item.filename
    self.cached_file_size = msiecf_item.cached_file_size

    self.cache_directory_index = msiecf_item.cache_directory_index
    if (msiecf_item.cache_directory_index >= 0 and
        msiecf_item.cache_directory_index < len(cache_directories)):
      self.cache_directory_name = (
          cache_directories[msiecf_item.cache_directory_index])


class MsiecfRedirectedEvent(time_events.TimestampEvent):
  """Convenience class for an MSIECF redirected event."""

  DATA_TYPE = 'msiecf:redirected'

  def __init__(self, msiecf_item, recovered=False):
    """Initializes the event.

    Args:
      msiecf_item: The MSIECF item (pymsiecf.leak).
      recovered: Boolean value to indicate the item was recovered, False
                 by default.
    """
    super(MsiecfRedirectedEvent, self).__init__(
        timelib.Timestamp.NONE_TIMESTAMP,
        eventdata.EventTimestamp.NOT_A_TIME)

    self.recovered = recovered
    self.location = msiecf_item.location


class MsiecfUrlEvent(time_events.TimestampEvent):
  """Convenience class for an MSIECF URL event."""

  DATA_TYPE = 'msiecf:url'

  def __init__(
      self, timestamp, timestamp_description, cache_directories, msiecf_item,
      recovered=False):
    """Initializes the event.

    Args:
      timestamp: The timestamp value.
      timestamp_description: The usage string describing the timestamp.
      cache_directories: A list of cache directory names.
      msiecf_item: The MSIECF item (pymsiecf.url).
      recovered: Boolean value to indicate the item was recovered, False
                 by default.
    """
    super(MsiecfUrlEvent, self).__init__(timestamp, timestamp_description)

    self.recovered = recovered
    self.offset = msiecf_item.offset

    self.url = msiecf_item.location
    self.number_of_hits = msiecf_item.number_of_hits
    self.cached_filename = msiecf_item.filename
    self.cached_file_size = msiecf_item.cached_file_size

    self.cache_directory_index = msiecf_item.cache_directory_index
    if (msiecf_item.cache_directory_index >= 0 and
        msiecf_item.cache_directory_index < len(cache_directories)):
      self.cache_directory_name = (
          cache_directories[msiecf_item.cache_directory_index])

    if msiecf_item.type and msiecf_item.data:
      if msiecf_item.type == u'cache':
        if msiecf_item.data[:4] == b'HTTP':
          self.http_headers = msiecf_item.data[:-1]
      # TODO: parse data of other URL item type like history which requires
      # OLE VT parsing.


class MsiecfParser(interface.BaseParser):
  """Parses MSIE Cache Files (MSIECF)."""

  NAME = u'msiecf'
  DESCRIPTION = u'Parser for MSIE Cache Files (MSIECF) also known as index.dat.'

  def _Parseleak(
      self, parser_mediator, cache_directories, msiecf_item, recovered=False):
    """Extract data from a MSIE Cache Files (MSIECF) leak item.

       Every item is stored as an event object, one for each timestamp.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      cache_directories: A list of cache directory names.
      msiecf_item: An item (pymsiecf.leak).
      recovered: Boolean value to indicate the item was recovered, False
                 by default.
    """
    # TODO: add support for possible last cache synchronization date and time.
    timestamp = timelib.Timestamp.NONE_TIMESTAMP
    timestamp_description = eventdata.EventTimestamp.NOT_A_TIME

    event_object = MsiecfLeakEvent(
        timestamp, timestamp_description, cache_directories, msiecf_item,
        recovered=recovered)
    parser_mediator.ProduceEvent(event_object)

  def _ParseRedirected(
      self, parser_mediator, msiecf_item, recovered=False):
    """Extract data from a MSIE Cache Files (MSIECF) redirected item.

       Every item is stored as an event object, one for each timestamp.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      msiecf_item: An item (pymsiecf.redirected).
      recovered: Boolean value to indicate the item was recovered, False
                 by default.
    """
    event_object = MsiecfRedirectedEvent(msiecf_item, recovered=recovered)
    parser_mediator.ProduceEvent(event_object)

  def _ParseUrl(
      self, parser_mediator, format_version, cache_directories, msiecf_item,
      recovered=False):
    """Extract data from a MSIE Cache Files (MSIECF) URL item.

       Every item is stored as an event object, one for each timestamp.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      format_version: The MSIECF format version.
      cache_directories: A list of cache directory names.
      msiecf_item: An item (pymsiecf.url).
      recovered: Boolean value to indicate the item was recovered, False
                 by default.
    """
    # The secondary timestamp can be stored in either UTC or local time
    # this is dependent on what the index.dat file is used for.
    # Either the file path or location string can be used to distinguish
    # between the different type of files.
    primary_timestamp = timelib.Timestamp.FromFiletime(
        msiecf_item.get_primary_time_as_integer())
    primary_timestamp_description = u'Primary Time'

    # Need to convert the FILETIME to the internal timestamp here to
    # do the from localtime conversion.
    secondary_timestamp = timelib.Timestamp.FromFiletime(
        msiecf_item.get_secondary_time_as_integer())
    secondary_timestamp_description = u'Secondary Time'

    if msiecf_item.type:
      if msiecf_item.type == u'cache':
        primary_timestamp_description = eventdata.EventTimestamp.ACCESS_TIME
        secondary_timestamp_description = (
            eventdata.EventTimestamp.MODIFICATION_TIME)

      elif msiecf_item.type == u'cookie':
        primary_timestamp_description = eventdata.EventTimestamp.ACCESS_TIME
        secondary_timestamp_description = (
            eventdata.EventTimestamp.MODIFICATION_TIME)

      elif msiecf_item.type == u'history':
        primary_timestamp_description = (
            eventdata.EventTimestamp.LAST_VISITED_TIME)
        secondary_timestamp_description = (
            eventdata.EventTimestamp.LAST_VISITED_TIME)

      elif msiecf_item.type == u'history-daily':
        primary_timestamp_description = (
            eventdata.EventTimestamp.LAST_VISITED_TIME)
        secondary_timestamp_description = (
            eventdata.EventTimestamp.LAST_VISITED_TIME)
        # The secondary_timestamp is in localtime normalize it to be in UTC.
        secondary_timestamp = timelib.Timestamp.LocaltimeToUTC(
            secondary_timestamp, parser_mediator.timezone)

      elif msiecf_item.type == u'history-weekly':
        primary_timestamp_description = eventdata.EventTimestamp.CREATION_TIME
        secondary_timestamp_description = (
            eventdata.EventTimestamp.LAST_VISITED_TIME)
        # The secondary_timestamp is in localtime normalize it to be in UTC.
        secondary_timestamp = timelib.Timestamp.LocaltimeToUTC(
            secondary_timestamp, parser_mediator.timezone)

    event_object = MsiecfUrlEvent(
        primary_timestamp, primary_timestamp_description, cache_directories,
        msiecf_item, recovered=recovered)
    parser_mediator.ProduceEvent(event_object)

    if secondary_timestamp > 0:
      event_object = MsiecfUrlEvent(
          secondary_timestamp, secondary_timestamp_description,
          cache_directories, msiecf_item, recovered=recovered)
      parser_mediator.ProduceEvent(event_object)

    expiration_timestamp = msiecf_item.get_expiration_time_as_integer()
    if expiration_timestamp > 0:
      # The expiration time in MSIECF version 4.7 is stored as a FILETIME value
      # in version 5.2 it is stored as a FAT date time value.
      # Since the as_integer function returns the raw integer value we need to
      # apply the right conversion here.
      if format_version == u'4.7':
        event_object = MsiecfUrlEvent(
            timelib.Timestamp.FromFiletime(expiration_timestamp),
            eventdata.EventTimestamp.EXPIRATION_TIME, cache_directories,
            msiecf_item, recovered=recovered)
      else:
        event_object = MsiecfUrlEvent(
            timelib.Timestamp.FromFatDateTime(expiration_timestamp),
            eventdata.EventTimestamp.EXPIRATION_TIME, cache_directories,
            msiecf_item, recovered=recovered)

      parser_mediator.ProduceEvent(event_object)

    last_checked_timestamp = msiecf_item.get_last_checked_time_as_integer()
    if last_checked_timestamp > 0:
      event_object = MsiecfUrlEvent(
          timelib.Timestamp.FromFatDateTime(last_checked_timestamp),
          eventdata.EventTimestamp.LAST_CHECKED_TIME, cache_directories,
          msiecf_item, recovered=recovered)
      parser_mediator.ProduceEvent(event_object)

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(
        b'Client\x20UrlCache\x20MMF\x20Ver\x20', offset=0)
    return format_specification

  def Parse(self, parser_mediator, **kwargs):
    """Parses a MSIE Cache File (MSIECF).

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_object = parser_mediator.GetFileObject()
    try:
      self.ParseFileObject(parser_mediator, file_object)
    finally:
      file_object.close()

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a MSIE Cache File (MSIECF) file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    msiecf_file = pymsiecf.file()
    msiecf_file.set_ascii_codepage(parser_mediator.codepage)

    try:
      msiecf_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceParseError(
          u'Unable to open file with error: {0:s}'.format(exception))
      return

    format_version = msiecf_file.format_version
    cache_directories = []
    for cache_directory_name in msiecf_file.cache_directories:
      cache_directories.append(cache_directory_name)

    for item_index in range(0, msiecf_file.number_of_items):
      try:
        msiecf_item = msiecf_file.get_item(item_index)
        if isinstance(msiecf_item, pymsiecf.leak):
          self._ParseLeak(parser_mediator, cache_directories, msiecf_item)

        elif isinstance(msiecf_item, pymsiecf.redirected):
          self._ParseRedirected(
              parser_mediator, cache_directories, msiecf_item)

        elif isinstance(msiecf_item, pymsiecf.url):
          self._ParseUrl(
              parser_mediator, format_version, cache_directories, msiecf_item)

      except IOError as exception:
        parser_mediator.ProduceParseError(
            u'Unable to parse item: {0:d} with error: {1:s}'.format(
                item_index, exception))

    for item_index in range(0, msiecf_file.number_of_recovered_items):
      try:
        msiecf_item = msiecf_file.get_recovered_item(item_index)
        if isinstance(msiecf_item, pymsiecf.leak):
          self._ParseLeak(
              parser_mediator, cache_directories, msiecf_item, recovered=True)

        elif isinstance(msiecf_item, pymsiecf.redirected):
          self._ParseRedidrected(
              parser_mediator, cache_directories, msiecf_item, recovered=True)

        elif isinstance(msiecf_item, pymsiecf.url):
          self._ParseUrl(
              parser_mediator, format_version, cache_directories, msiecf_item,
              recovered=True)

      except IOError as exception:
        parser_mediator.ProduceParseError(
            u'Unable to parse recovered item: {0:d} with error: {1:s}'.format(
                item_index, exception))

    msiecf_file.close()


manager.ParsersManager.RegisterParser(MsiecfParser)
