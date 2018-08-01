# -*- coding: utf-8 -*-
"""Parser for the Microsoft File History ESE database."""

from __future__ import unicode_literals

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

  DATA_TYPE = 'file_history:namespace:event'

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

  NAME = 'file_history'
  DESCRIPTION = 'Parser for File History ESE database files.'

  # TODO: Add support for other tables as well, backupset, file, library, etc.
  REQUIRED_TABLES = {
      'backupset': '',
      'file': '',
      'library': '',
      'namespace': 'ParseNameSpace'}

  def _GetDictFromStringsTable(self, parser_mediator, table):
    """Build a dictionary of the value in the strings table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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

  # pylint 1.9.3 wants a docstring for kwargs, but this is not useful to add.
  # pylint: disable=missing-param-doc,unused-argument
  def ParseNameSpace(
      self, parser_mediator, cache=None, database=None, table=None,
      **unused_kwargs):
    """Parses the namespace table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      cache (Optional[ESEDBCache]): cache.
      database (Optional[pyesedb.file]): ESE database.
      table (Optional[pyesedb.table]): table.

    Raises:
      ValueError: if the database or table value is missing.
    """
    if database is None:
      raise ValueError('Missing database value.')

    if table is None:
      raise ValueError('Missing table value.')

    strings = cache.GetResults('strings')
    if not strings:
      esedb_table = database.get_table_by_name('string')
      strings = self._GetDictFromStringsTable(parser_mediator, esedb_table)
      cache.StoreDictInCache('strings', strings)

    for esedb_record in table.records:
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, table.name, esedb_record)

      event_data = FileHistoryNamespaceEventData()
      event_data.file_attribute = record_values.get('fileAttrib', None)
      event_data.identifier = record_values.get('id', None)
      event_data.parent_identifier = record_values.get('parentId', None)
      event_data.usn_number = record_values.get('usn', None)
      event_data.original_filename = strings.get(event_data.identifier, None)

      created_timestamp = record_values.get('fileCreated')
      if created_timestamp:
        date_time = dfdatetime_filetime.Filetime(timestamp=created_timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_CREATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      modified_timestamp = record_values.get('fileModified')
      if modified_timestamp:
        date_time = dfdatetime_filetime.Filetime(timestamp=modified_timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      if not created_timestamp and not modified_timestamp:
        date_time = dfdatetime_semantic_time.SemanticTime('Not set')
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
        parser_mediator.ProduceEventWithEventData(event, event_data)


esedb.ESEDBParser.RegisterPlugin(FileHistoryESEDBPlugin)
