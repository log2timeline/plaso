# -*- coding: utf-8 -*-
"""Parser for the System Resource Usage Monitor (SRUM) ESE database."""

from __future__ import unicode_literals

import logging

import construct
import pyfwnt

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import ole_automation_date as dfdatetime_ole_automation_date
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface


class SRUMApplicationResourceUsageEventData(events.EventData):
  """SRUM application resource usage event data.

  Attributes:
    application_identifier (int): application identifier.
    background_bytes_read (int): background number of bytes read.
    background_bytes_written (int): background number of bytes written.
    background_context_switches (int): number of background context switches.
    background_cycle_time (int): background cycle time.
    background_number_for_flushes (int): background number of flushes.
    background_number_for_read_operations (int): background number of read
        operations.
    background_number_for_write_operations (int): background number of write
        operations.
    face_time (int): face time.
    foreground_bytes_read (int): foreground number of bytes read.
    foreground_bytes_written (int): foreground number of bytes written.
    foreground_context_switches (int): number of foreground context switches.
    foreground_cycle_time (int): foreground cycle time.
    foreground_number_for_flushes (int): foreground number of flushes.
    foreground_number_for_read_operations (int): foreground number of read
        operations.
    foreground_number_for_write_operations (int): foreground number of write
        operations.
    identifier (int): record identifier.
    user_identifier (int): user identifier.
  """

  DATA_TYPE = 'windows:srum:application_usage'

  def __init__(self):
    """Initializes event data."""
    super(SRUMApplicationResourceUsageEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.application_identifier = None
    self.background_bytes_read = None
    self.background_bytes_written = None
    self.background_context_switches = None
    self.background_cycle_time = None
    self.background_number_for_flushes = None
    self.background_number_for_read_operations = None
    self.background_number_for_write_operations = None
    self.face_time = None
    self.foreground_bytes_read = None
    self.foreground_bytes_written = None
    self.foreground_context_switches = None
    self.foreground_cycle_time = None
    self.foreground_number_for_flushes = None
    self.foreground_number_for_read_operations = None
    self.foreground_number_for_write_operations = None
    self.identifier = None
    self.user_identifier = None


class SRUMNetworkConnectivityUsageEventData(events.EventData):
  """SRUM network connectivity usage event data.

  Attributes:
    application_identifier (int): application identifier.
    identifier (int): record identifier.
    interface_luid (int): interface locally unique identifier (LUID).
    l2_profile_flags (int): L2 profile flags.
    l2_profile_identifier (int): L2 profile identifier.
    user_identifier (int): user identifier.
  """

  DATA_TYPE = 'windows:srum:network_connectivity'

  def __init__(self):
    """Initializes event data."""
    super(SRUMNetworkConnectivityUsageEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.application_identifier = None
    self.identifier = None
    self.interface_luid = None
    self.l2_profile_flags = None
    self.l2_profile_identifier = None
    self.user_identifier = None


class SRUMNetworkDataUsageEventData(events.EventData):
  """SRUM network data usage event data.

  Attributes:
    application_identifier (int): application identifier.
    bytes_received (int): number of bytes received.
    bytes_sent (int): number of bytes sent.
    identifier (int): record identifier.
    interface_luid (int): interface locally unique identifier (LUID).
    l2_profile_flags (int): L2 profile flags.
    l2_profile_identifier (int): L2 profile identifier.
    user_identifier (int): user identifier.
  """

  DATA_TYPE = 'windows:srum:network_usage'

  def __init__(self):
    """Initializes event data."""
    super(SRUMNetworkDataUsageEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.application_identifier = None
    self.bytes_received = None
    self.bytes_sent = None
    self.identifier = None
    self.interface_luid = None
    self.l2_profile_flags = None
    self.l2_profile_identifier = None
    self.user_identifier = None


class SystemResourceUsageMonitorESEDBPlugin(interface.ESEDBPlugin):
  """Parses a System Resource Usage Monitor (SRUM) ESE database file."""

  NAME = 'esedb_srum'
  DESCRIPTION = (
      'Parser for System Resource Usage Monitor (SRUM) ESE database files.')

  # TODO: add support for tables:
  # {5C8CF1C7-7257-4F13-B223-970EF5939312}
  # {97C2CE28-A37B-4920-B1E9-8B76CD341EC5}
  # {B6D82AF1-F780-4E17-8077-6CB9AD8A6FC4}
  # {D10CA2FE-6FCF-4F6D-848E-B2E99266FA86}
  # {DA73FB89-2BEA-4DDC-86B8-6E048C6DA477}
  # {FEE4E14F-02A9-4550-B5CE-5FA2DA202E37}

  OPTIONAL_TABLES = {
      '{973F5D5C-1D90-4944-BE8E-24B94231A174}': 'ParseNetworkDataUsage',
      '{D10CA2FE-6FCF-4F6D-848E-B2E99266FA89}': 'ParseApplicationResourceUsage',
      '{DD6636C4-8929-4683-974E-22C046A43763}': 'ParseNetworkConnectivityUsage'}

  REQUIRED_TABLES = {
      'SruDbIdMapTable': ''}

  _GUID_TABLE_VALUE_MAPPINGS = {
      'TimeStamp': '_ConvertValueBinaryDataToFloatingPointValue'}

  _FLOAT32_LITTLE_ENDIAN = construct.LFloat32('float32')
  _FLOAT64_LITTLE_ENDIAN = construct.LFloat64('float64')

  _APPLICATION_RESOURCE_USAGE_VALUES_MAP = {
      'application_identifier': 'AppId',
      'background_bytes_read': 'BackgroundBytesRead',
      'background_bytes_written': 'BackgroundBytesWritten',
      'background_context_switches': 'BackgroundContextSwitches',
      'background_cycle_time': 'BackgroundCycleTime',
      'background_number_for_flushes': 'BackgroundNumberOfFlushes',
      'background_number_for_read_operations': 'BackgroundNumReadOperations',
      'background_number_for_write_operations': 'BackgroundNumWriteOperations',
      'face_time': 'FaceTime',
      'foreground_bytes_read': 'ForegroundBytesRead',
      'foreground_bytes_written': 'ForegroundBytesWritten',
      'foreground_context_switches': 'ForegroundContextSwitches',
      'foreground_cycle_time': 'ForegroundCycleTime',
      'foreground_number_for_flushes': 'ForegroundNumberOfFlushes',
      'foreground_number_for_read_operations': 'ForegroundNumReadOperations',
      'foreground_number_for_write_operations': 'ForegroundNumWriteOperations',
      'identifier': 'AutoIncId',
      'user_identifier': 'UserId'}

  _NETWORK_CONNECTIVITY_USAGE_VALUES_MAP = {
      'application_identifier': 'AppId',
      'connected_time': 'ConnectedTime',
      'identifier': 'AutoIncId',
      'interface_luid': 'InterfaceLuid',
      'l2_profile_flags': 'L2ProfileFlags',
      'l2_profile_identifier': 'L2ProfileId',
      'user_identifier': 'UserId'}

  _NETWORK_DATA_USAGE_VALUES_MAP = {
      'application_identifier': 'AppId',
      'bytes_recieved': 'BytesRecvd',
      'bytes_sent': 'BytesSent',
      'identifier': 'AutoIncId',
      'interface_luid': 'InterfaceLuid',
      'l2_profile_flags': 'L2ProfileFlags',
      'l2_profile_identifier': 'L2ProfileId',
      'user_identifier': 'UserId'}

  def _ConvertValueBinaryDataToFloatingPointValue(self, value):
    """Converts a binary data value into a floating-point value.

    Args:
      value (bytes): binary data value containing an ASCII string or None.

    Returns:
      float: floating-point representation of binary data value or None.
    """
    if value:
      value_length = len(value)
      if value_length == 4:
        return self._FLOAT32_LITTLE_ENDIAN.parse(value)
      elif value_length == 8:
        return self._FLOAT64_LITTLE_ENDIAN.parse(value)

  def _GetIdentifierMappings(self, parser_mediator, cache, database):
    """Retrieves the identifier mappings from SruDbIdMapTable table.

    Identifier mappings are stored in the cache for optimization.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      cache (ESEDBCache): cache, which contains information about
          the identifiers stored in the SruDbIdMapTable table.
      database (pyesedb.file): ESE database.

    Returns:
      dict[str, str]: mapping of identifiers to their string representation.
    """
    identifier_mappings = cache.GetResults('SruDbIdMapTable', default_value={})
    if identifier_mappings:
      return identifier_mappings

    esedb_table = database.get_table_by_name('SruDbIdMapTable')
    if not esedb_table:
      parser_mediator.ProduceExtractionError(
          'unable to retrieve table: SruDbIdMapTable')
      cache.StoreDictInCache('SruDbIdMapTable', {})
      return identifier_mappings

    for esedb_record in esedb_table.records:
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, esedb_table.name, esedb_record)

      identifier = record_values.get('IdIndex', None)
      if identifier is None:
        parser_mediator.ProduceExtractionError(
            'column: IdIndex missing from parse table: SruDbIdMapTable')
        continue

      identifier_type = record_values.get('IdType', None)
      if identifier_type is None:
        parser_mediator.ProduceExtractionError(
            'column: IdType missing from parse table: SruDbIdMapTable')
        continue

      mapping = record_values.get('IdBlob', None)
      if mapping is None:
        parser_mediator.ProduceExtractionError(
            'column: IdBlob missing from parse table: SruDbIdMapTable')
        continue

      if identifier_type in (0, 1, 2):
        try:
          mapping = mapping.decode('utf-16le')
        except UnicodeDecodeError:
          parser_mediator.ProduceExtractionError(
              'column: IdBlob missing from parse table: SruDbIdMapTable')
          continue

      elif identifier_type == 3:
         # TODO: convert byte stream to SID
         pass

         # fwnt_identifier = pyfwnt.security_identifier()
         # fwnt_identifier.copy_from_byte_stream(mapping)
         # mapping = fwnt_identifier.get_string()

      else:
        parser_mediator.ProduceExtractionError(
            'unsupported identifier type: {0:d}'.format(identifier_type))
        continue

      if identifier in identifier_mappings:
        parser_mediator.ProduceExtractionError(
            'identifier: {0:d} already exists in mappings.'.format(identifier))
        continue

      identifier_mappings[identifier] = mapping

    cache.StoreDictInCache('SruDbIdMapTable', identifier_mappings)
    return identifier_mappings

  def _ParseGUIDTable(
      self, parser_mediator, cache, database, esedb_table, values_map,
      event_data_class):
    """Parses a table with a GUID as name.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      cache (ESEDBCache): cache, which contains information about
          the identifiers stored in the SruDbIdMapTable table.
      database (pyesedb.file): ESE database.
      esedb_table (pyesedb.table): table.
      values_map (dict[str, str]): maps table column names to attribute names.
      event_data_class (type): event data class.
    """
    if cache is None:
      logging.warning('[{0:s}] invalid cache'.format(self.NAME))
      return

    if database is None:
      logging.warning('[{0:s}] invalid database'.format(self.NAME))
      return

    if esedb_table is None:
      logging.warning('[{0:s}] invalid table'.format(self.NAME))
      return

    identifier_mappings = self._GetIdentifierMappings(
        parser_mediator, cache, database)

    for esedb_record in esedb_table.records:
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, esedb_table.name, esedb_record,
          value_mappings=self._GUID_TABLE_VALUE_MAPPINGS)

      event_data = event_data_class()

      for attribute_name, column_name in values_map.items():
        record_value = record_values.get(column_name, None)
        if attribute_name == 'AppId':
          record_value = identifier_mappings.get(record_value, record_value)

        setattr(event_data, attribute_name, record_value)

      timestamp = record_values.get('TimeStamp')
      if timestamp:
        date_time = dfdatetime_ole_automation_date.OLEAutomationDate(
            timestamp=timestamp)
        timestamp_description = definitions.TIME_DESCRIPTION_SAMPLE
      else:
        date_time = dfdatetime_semantic_time.SemanticTime('Not set')
        timestamp_description = definitions.TIME_DESCRIPTION_NOT_A_TIME

      event = time_events.DateTimeValuesEvent(date_time, timestamp_description)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      timestamp = record_values.get('ConnectStartTime')
      if timestamp:
        date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_FIRST_CONNECTED)
        parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseApplicationResourceUsage(
      self, parser_mediator, cache=None, database=None, table=None,
      **unused_kwargs):
    """Parses the application resource usage table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      cache (Optional[ESEDBCache]): cache, which contains information about
          the identifiers stored in the SruDbIdMapTable table.
      database (Optional[pyesedb.file]): ESE database.
      table (Optional[pyesedb.table]): table.
    """
    self._ParseGUIDTable(
        parser_mediator, cache, database, table,
        self._APPLICATION_RESOURCE_USAGE_VALUES_MAP,
        SRUMApplicationResourceUsageEventData)

  def ParseNetworkDataUsage(
      self, parser_mediator, cache=None, database=None, table=None,
      **unused_kwargs):
    """Parses the network data usage monitor table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      cache (Optional[ESEDBCache]): cache, which contains information about
          the identifiers stored in the SruDbIdMapTable table.
      database (Optional[pyesedb.file]): ESE database.
      table (Optional[pyesedb.table]): table.
    """
    self._ParseGUIDTable(
        parser_mediator, cache, database, table,
        self._NETWORK_DATA_USAGE_VALUES_MAP, SRUMNetworkDataUsageEventData)

  def ParseNetworkConnectivityUsage(
      self, parser_mediator, cache=None, database=None, table=None,
      **unused_kwargs):
    """Parses the network connectivity usage monitor table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      cache (Optional[ESEDBCache]): cache, which contains information about
          the identifiers stored in the SruDbIdMapTable table.
      database (Optional[pyesedb.file]): ESE database.
      table (Optional[pyesedb.table]): table.
    """
    # TODO: consider making ConnectStartTime + ConnectedTime an event.
    self._ParseGUIDTable(
        parser_mediator, cache, database, table,
        self._NETWORK_CONNECTIVITY_USAGE_VALUES_MAP,
        SRUMNetworkConnectivityUsageEventData)


esedb.ESEDBParser.RegisterPlugin(SystemResourceUsageMonitorESEDBPlugin)
