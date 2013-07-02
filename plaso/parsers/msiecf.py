#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Parser for Microsoft Internet Explorer (MSIE) Cache Files (CF)."""
import logging

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import timelib

import pymsiecf


if pymsiecf.get_version() < '20130317':
  raise ImportWarning('MsiecfParser requires at least pymsiecf 20130317.')


class MsiecfUrlEventContainer(event.EventContainer):
  """Convenience class for an MSIECF URL event container."""
  def __init__(self, msiecf_item, recovered=False):
    """Initializes the event container.

    Args:
      msiecf_item: The MSIECF item (pymsiecf.url).
      recovered: Boolean value to indicate the item was recovered, False
                 by default.
    """
    super(MsiecfUrlEventContainer, self).__init__()
    self.data_type = 'msiecf:url'

    self.recovered = recovered
    self.offset = msiecf_item.offset

    self.url = msiecf_item.location
    self.number_of_hits = msiecf_item.number_of_hits
    self.cache_directory_index = msiecf_item.cache_directory_index
    self.filename = msiecf_item.filename
    self.cached_file_size = msiecf_item.cached_file_size

    if msiecf_item.type and msiecf_item.data:
      if msiecf_item.type == u'cache':
        if msiecf_item.data[:4] == 'HTTP':
          self.http_headers = msiecf_item.data[:-1]
      # TODO: parse data of other URL item type like history which requires
      # OLE VT parsing.


class MsiecfParser(parser.PlasoParser):
  """Parses MSIE Cache Files (MSIECF)."""

  def _ParseUrl(self, pre_obj, msiecf_item, recovered=False):
    """Extract data from a MSIE Cache Files (MSIECF) URL item.

       Every item is stored in an event container with 4 sub event objects
       one for each timestamp.

    Args:
      pre_obj: An instance of the preprocessor object.
      msiecf_item: An item (pymsiecf.url).
      recovered: Boolean value to indicate the item was recovered, False
                 by default.

    Returns:
      An event container (MsiecfUrlEventContainer) that contains
      the parsed data.
    """
    event_container = MsiecfUrlEventContainer(msiecf_item, recovered)

    # The secondary timestamp can be stored in either UTC or local time
    # this is dependent on what the index.dat file is used for.
    # Either the file path of the location string can be used to distinguish
    # between the different type of files.
    primary_timestamp = msiecf_item.get_primary_time_as_integer()
    primary_timestamp_desc = 'Primary Time'

    # Need to convert the FILETIME to the internal timestamp here to
    # do the from localtime conversion.
    secondary_timestamp = timelib.Timestamp.FromFiletime(
        msiecf_item.get_secondary_time_as_integer())
    secondary_timestamp_desc = 'Secondary Time'

    if msiecf_item.type:
      if msiecf_item.type == u'cache':
        primary_timestamp_desc = eventdata.EventTimestamp.ACCESS_TIME
        secondary_timestamp_desc = eventdata.EventTimestamp.MODIFICATION_TIME

      elif msiecf_item.type == u'cookie':
        primary_timestamp_desc = eventdata.EventTimestamp.ACCESS_TIME
        secondary_timestamp_desc = eventdata.EventTimestamp.MODIFICATION_TIME

      elif msiecf_item.type == u'history':
        primary_timestamp_desc = eventdata.EventTimestamp.LAST_VISITED_TIME
        secondary_timestamp_desc = eventdata.EventTimestamp.LAST_VISITED_TIME

      elif msiecf_item.type == u'history-daily':
        primary_timestamp_desc = eventdata.EventTimestamp.LAST_VISITED_TIME
        secondary_timestamp_desc = eventdata.EventTimestamp.LAST_VISITED_TIME
        # The secondary_timestamp is in localtime normalize it to be in UTC.
        secondary_timestamp = timelib.Timestamp.LocaltimeToUTC(
            secondary_timestamp, pre_obj.zone)

      elif msiecf_item.type == u'history-weekly':
        primary_timestamp_desc = eventdata.EventTimestamp.CREATION_TIME
        secondary_timestamp_desc = eventdata.EventTimestamp.LAST_VISITED_TIME
        # The secondary_timestamp is in localtime normalize it to be in UTC.
        secondary_timestamp = timelib.Timestamp.LocaltimeToUTC(
            secondary_timestamp, pre_obj.zone)

    event_container.Append(event.FiletimeEvent(
        primary_timestamp, primary_timestamp_desc, event_container.data_type))

    if secondary_timestamp > 0:
      event_container.Append(event.TimestampEvent(
          secondary_timestamp, secondary_timestamp_desc,
          event_container.data_type))

    expiration_timestamp = msiecf_item.get_expiration_time_as_integer()
    if expiration_timestamp > 0:
      # The expiration time in MSIECF version 4.7 is stored as a FILETIME value
      # in version 5.2 it is stored as a FAT date time value.
      # Since the as_integer function returns the raw integer value we need to
      # apply the right conversion here.
      if self.version == u'4.7':
        event_container.Append(event.FiletimeEvent(
            expiration_timestamp, eventdata.EventTimestamp.EXPIRATION_TIME,
            event_container.data_type))
      else:
        event_container.Append(event.FatDateTimeEvent(
            expiration_timestamp, eventdata.EventTimestamp.EXPIRATION_TIME,
            event_container.data_type))

    last_checked_timestamp = msiecf_item.get_last_checked_time_as_integer()
    if last_checked_timestamp > 0:
      event_container.Append(event.FatDateTimeEvent(
          last_checked_timestamp, 'Last Checked Time',
          event_container.data_type))

    return event_container

  def Parse(self, file_object):
    """Extract data from a MSIE Cache File (MSIECF).

       A separate event container is returned for every item to limit
       memory consumption.

    Args:
      file_object: A file-like object to read data from.

    Yields:
      An event container (MsiecfUrlEventContainer) that contains
      the parsed data.
    """
    msiecf_file = pymsiecf.file()
    msiecf_file.set_ascii_codepage(getattr(self._pre_obj, 'codepage', 'cp1252'))

    try:
      msiecf_file.open_file_object(file_object)

      self.version = msiecf_file.format_version
    except IOError as exception:
      raise errors.UnableToParseFile('[%s] unable to parse file %s: %s' % (
          self.parser_name, file_object.name, exception))

    for item_index in range(0, msiecf_file.number_of_items):
      try:
        msiecf_item = msiecf_file.get_item(item_index)
        if isinstance(msiecf_item, pymsiecf.url):
          yield self._ParseUrl(self._pre_obj, msiecf_item)
        # TODO: implement support for pymsiecf.leak, pymsiecf.redirected,
        # pymsiecf.item.
      except IOError as exception:
        logging.warning('[%s] unable to parse item: %d in file: %s: %s' % (
            self.parser_name, item_index, file_object.name, exception))

    for item_index in range(0, msiecf_file.number_of_recovered_items):
      try:
        msiecf_item = msiecf_file.get_recovered_item(item_index)
        if isinstance(msiecf_item, pymsiecf.url):
          yield self._ParseUrl(self._pre_obj, msiecf_item, recovered=True)
        # TODO: implement support for pymsiecf.leak, pymsiecf.redirected,
        # pymsiecf.item.
      except IOError as exception:
        logging.info(
            '[%s] unable to parse recovered item: %d in file: %s: %s' % (
            self.parser_name, item_index, file_object.name, exception))
