# -*- coding: utf-8 -*-
"""Parser for the Microsoft File History ESE database."""

from plaso.containers import events
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface


class FileHistoryNamespaceEventData(events.EventData):
  """File history namespace table event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): file entry creation date
        and time.
    file_attribute (int): file attribute.
    identifier (str): identifier.
    modification_time (dfdatetime.DateTimeValues): file entry last modification
        date and time.
    original_filename (str): original file name.
    parent_identifier (str): parent identifier.
    usn_number (int): USN number.
  """

  DATA_TYPE = 'windows:file_history:namespace'

  def __init__(self):
    """Initializes event data."""
    super(FileHistoryNamespaceEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.creation_time = None
    self.file_attribute = None
    self.identifier = None
    self.modification_time = None
    self.original_filename = None
    self.parent_identifier = None
    self.usn_number = None


class FileHistoryESEDBPlugin(interface.ESEDBPlugin):
  """Parses a File History ESE database file."""

  NAME = 'file_history'
  DATA_FORMAT = 'Windows 8 File History ESE database file'

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
          and other components, such as storage and dfVFS.
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
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      cache (Optional[ESEDBCache]): cache.
      database (Optional[ESEDatabase]): ESE database.
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
      esedb_table = database.GetTableByName('string')
      strings = self._GetDictFromStringsTable(parser_mediator, esedb_table)
      cache.StoreDictInCache('strings', strings)

    for record_index, esedb_record in enumerate(table.records):
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, table.name, record_index, esedb_record)

      event_data = FileHistoryNamespaceEventData()
      event_data.creation_time = self._GetFiletimeRecordValue(
           record_values, 'fileCreated')
      event_data.file_attribute = record_values.get('fileAttrib', None)
      event_data.identifier = record_values.get('id', None)
      event_data.modification_time = self._GetFiletimeRecordValue(
          record_values, 'fileModified')
      event_data.original_filename = strings.get(event_data.identifier, None)
      event_data.parent_identifier = record_values.get('parentId', None)
      event_data.usn_number = record_values.get('usn', None)

      parser_mediator.ProduceEventData(event_data)


esedb.ESEDBParser.RegisterPlugin(FileHistoryESEDBPlugin)
