#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Parser for the Microsoft File History ESE database."""

import logging

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface


class FileHistoryNamespaceEventObject(time_events.FiletimeEvent):
  """Convenience class for a file history namespace table event."""

  DATA_TYPE = 'file_history:namespace:event'

  def __init__(self, timestamp, usage, filename, record_values):
    """Initializes the event.

    Args:
      timestamp: The FILETIME timestamp value.
      usage: The usage string, describing the timdestamp value.
      filename: The name of the file.
      record_values: A dict object containing the record values.
    """
    super(FileHistoryNamespaceEventObject, self).__init__(timestamp, usage)

    self.file_attribute = record_values.get(u'fileAttrib')
    self.identifier = record_values.get(u'id')
    self.original_filename = filename
    self.parent_identifier = record_values.get(u'parentId')
    self.usn_number = record_values.get(u'usn')


class FileHistoryEseDbPlugin(interface.EseDbPlugin):
  """Parses a File History ESE database file."""

  NAME = 'esedb_file_history'
  DESCRIPTION = u'Parser for File History ESE database files.'

  # TODO: Add support for other tables as well, backupset, file, library, etc.
  REQUIRED_TABLES = {
      'backupset': '',
      'file': '',
      'library': '',
      'namespace': 'ParseNameSpace'}

  def _GetDictFromStringsTable(self, table):
    """Build a dict for the strings table.

    Args:
      table: A table object for the strings table (instance of pyesedb.table).

    Returns:
      A dict that contains the identification field as key and filename as
      value.
    """
    return_dict = {}

    if not table:
      return return_dict

    for record in table.records:
      if record.get_number_of_values() != 2:
        continue

      identification = self._GetRecordValue(record, 0)
      filename = self._GetRecordValue(record, 1)

      if not identification:
        continue
      return_dict[identification] = filename

    return return_dict

  def ParseNameSpace(
      self, parser_context, file_entry=None, parser_chain=None, database=None,
      cache=None, table=None, **unused_kwargs):
    """Parses the namespace table.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      database: Optional database object (instance of pyesedb.file).
                The default is None.
      cache: Optional cache object (instance of EseDbCache).
      table: Optional table object (instance of pyesedb.table).
             The default is None.
    """
    if database is None:
      logging.warning(u'[{0:s}] invalid database'.format(self.NAME))
      return

    if table is None:
      logging.warning(u'[{0:s}] invalid Containers table'.format(self.NAME))
      return

    strings = cache.GetResults('strings')
    if not strings:
      strings = self._GetDictFromStringsTable(
          database.get_table_by_name(u'string'))
      cache.StoreDictInCache(u'strings', strings)

    for esedb_record in table.records:
      record_values = self._GetRecordValues(table.name, esedb_record)

      filename = strings.get(record_values.get('id', -1), u'')
      created_timestamp = record_values.get(u'fileCreated')

      if created_timestamp:
        event_object = FileHistoryNamespaceEventObject(
            created_timestamp, eventdata.EventTimestamp.CREATION_TIME,
            filename, record_values)
        parser_context.ProduceEvent(
            event_object, parser_chain=parser_chain, file_entry=file_entry)

      modified_timestamp = record_values.get(u'fileModified')
      if modified_timestamp:
        event_object = FileHistoryNamespaceEventObject(
            modified_timestamp, eventdata.EventTimestamp.MODIFICATION_TIME,
            filename, record_values)
        parser_context.ProduceEvent(
            event_object, parser_chain=parser_chain, file_entry=file_entry)


esedb.EseDbParser.RegisterPlugin(FileHistoryEseDbPlugin)
