# -*- coding: utf-8 -*-
"""Parser for the Microsoft File History ESE database."""

import logging

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface


class FileHistoryNamespaceEventData(events.EventData):
  """File history namespace table event data.

  Attributes:
    file_attribute (int): file attribute.
    identifier (str): identifier.
    original_filename (str): original file name.
    parent_identifier (str): parent identifier.
    usn_number (int): USN number.
  """

  DATA_TYPE = u'file_history:namespace:event'

  def __init__(self):
    """Initializes event data."""
    super(FileHistoryNamespaceEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.file_attribute = None
    self.identifier = None
    self.original_filename = None
    self.parent_identifier = None
    self.usn_number = None


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

      event_data = FileHistoryNamespaceEventData()
      event_data.file_attribute = record_values.get(u'fileAttrib', None)
      event_data.identifier = record_values.get(u'id', None)
      event_data.parent_identifier = record_values.get(u'parentId', None)
      event_data.usn_number = record_values.get(u'usn', None)
      event_data.original_filename = strings.get(event_data.identifier, None)

      created_timestamp = record_values.get(u'fileCreated')
      if created_timestamp:
        date_time = dfdatetime_filetime.Filetime(timestamp=created_timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_CREATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      modified_timestamp = record_values.get(u'fileModified')
      if modified_timestamp:
        date_time = dfdatetime_filetime.Filetime(timestamp=modified_timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      if not created_timestamp and not modified_timestamp:
        date_time = dfdatetime_semantic_time.SemanticTime(u'Not set')
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
        parser_mediator.ProduceEventWithEventData(event, event_data)


esedb.ESEDBParser.RegisterPlugin(FileHistoryESEDBPlugin)
