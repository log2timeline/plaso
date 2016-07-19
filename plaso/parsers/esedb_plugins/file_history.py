# -*- coding: utf-8 -*-
"""Parser for the Microsoft File History ESE database."""

import logging

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface


class FileHistoryNamespaceEventObject(time_events.FiletimeEvent):
  """Convenience class for a file history namespace table event.

  Attributes:
    file_attribute (int): file attribute.
    identifier (int): identifier.
    original_filename (str): original file name.
    parent_identifier (int): parent identifier.
    usn_number (int): USN number.
  """

  DATA_TYPE = u'file_history:namespace:event'

  # TODO: replace record values by explicit arguments.
  def __init__(self, filetime, timestamp_description, filename, record_values):
    """Initializes the event.

    Args:
      filetime (int): FILETIME timestamp value.
      timestamp_description (str): description of the usage of the timestamp
          value.
      filename (srr): name of the orignal file.
      record_values (dict[str,object]): record values.
    """
    super(FileHistoryNamespaceEventObject, self).__init__(
        filetime, timestamp_description)

    self.file_attribute = record_values.get(u'fileAttrib')
    self.identifier = record_values.get(u'id')
    self.original_filename = filename
    self.parent_identifier = record_values.get(u'parentId')
    self.usn_number = record_values.get(u'usn')


class FileHistoryESEDBPlugin(interface.ESEDBPlugin):
  """Parses a File History ESE database file."""

  NAME = u'esedb_file_history'
  DESCRIPTION = u'Parser for File History ESE database files.'

  # TODO: Add support for other tables as well, backupset, file, library, etc.
  REQUIRED_TABLES = {
      u'backupset': u'',
      u'file': u'',
      u'library': u'',
      u'namespace': u'ParseNameSpace'}

  def _GetDictFromStringsTable(self, parser_mediator, table):
    """Build a dictionary of the value in the strings table.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      table (pyesedb.table): strings table.

    Returns:
      dict[str,object]: values per column name.
    """
    if not table:
      return {}

    record_values = {}
    for record in table.records:
      if parser_mediator.abort:
        break

      if record.get_number_of_values() != 2:
        continue

      identification = self._GetRecordValue(record, 0)
      filename = self._GetRecordValue(record, 1)

      if not identification:
        continue
      record_values[identification] = filename

    return record_values

  def ParseNameSpace(
      self, parser_mediator, cache=None, database=None, table=None,
      **unused_kwargs):
    """Parses the namespace table.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      cache (Optional[ESEDBCache]): cache.
      database (Optional[pyesedb.file]): ESE database.
      table (Optional[pyesedb.table]): table.
    """
    if database is None:
      logging.warning(u'[{0:s}] invalid database'.format(self.NAME))
      return

    if table is None:
      logging.warning(u'[{0:s}] invalid Containers table'.format(self.NAME))
      return

    strings = cache.GetResults(u'strings')
    if not strings:
      esedb_table = database.get_table_by_name(u'string')
      strings = self._GetDictFromStringsTable(parser_mediator, esedb_table)
      cache.StoreDictInCache(u'strings', strings)

    for esedb_record in table.records:
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, table.name, esedb_record)

      filename = strings.get(record_values.get(u'id', -1), u'')
      created_timestamp = record_values.get(u'fileCreated')

      if created_timestamp:
        event_object = FileHistoryNamespaceEventObject(
            created_timestamp, eventdata.EventTimestamp.CREATION_TIME,
            filename, record_values)
        parser_mediator.ProduceEvent(event_object)

      modified_timestamp = record_values.get(u'fileModified')
      if modified_timestamp:
        event_object = FileHistoryNamespaceEventObject(
            modified_timestamp, eventdata.EventTimestamp.MODIFICATION_TIME,
            filename, record_values)
        parser_mediator.ProduceEvent(event_object)


esedb.ESEDBParser.RegisterPlugin(FileHistoryESEDBPlugin)
