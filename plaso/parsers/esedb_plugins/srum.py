# -*- coding: utf-8 -*-
"""Parser for the System Resource Usage Monitor (SRUM) ESE database."""

from __future__ import unicode_literals

import logging

import construct

from dfdatetime import ole_automation_date as dfdatetime_ole_automation_date
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface


class SRUMNetworkDataUsageMonitorEventData(events.EventData):
  """SRUM network data usage monitor event data.

  Attributes:
    application_identifier (int): application identifier.
    bytes_received (int): number of bytes received.
    bytes_sent (int): number of bytes sent.
    identifier (int): record identifier.
    interface_luid (int): interface locally unique identifier (LUID).
    user_identifier (int): user identifier.
  """

  DATA_TYPE = 'windows:srum:network_usage'

  def __init__(self):
    """Initializes event data."""
    super(SRUMNetworkDataUsageMonitorEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.application_identifier = None
    self.bytes_received = None
    self.bytes_sent = None
    self.identifier = None
    self.interface_luid = None
    self.user_identifier = None

class SystemResourceUsageMonitorESEDBPlugin(interface.ESEDBPlugin):
  """Parses a System Resource Usage Monitor (SRUM) ESE database file."""

  NAME = 'esedb_srum'
  DESCRIPTION = (
      'Parser for System Resource Usage Monitor (SRUM) ESE database files.')

  REQUIRED_TABLES = {
      '{973F5D5C-1D90-4944-BE8E-24B94231A174}': 'ParseNetworkDataUsageMonitor',
      'SruDbIdMapTable': '',
      'SruDbCheckpointTable': ''}

  _GUID_TABLE_VALUE_MAPPINGS = {
      'TimeStamp': '_ConvertValueBinaryDataToFloatingPointValue'}

  _FLOAT32_LITTLE_ENDIAN = construct.LFloat32('float32')
  _FLOAT64_LITTLE_ENDIAN = construct.LFloat64('float64')

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

  def ParseNetworkDataUsageMonitor(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses the network data usage monitor table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      database (Optional[pyesedb.file]): ESE database.
      table (Optional[pyesedb.table]): table.
    """
    if database is None:
      logging.warning('[{0:s}] invalid database'.format(self.NAME))
      return

    if table is None:
      logging.warning('[{0:s}] invalid Containers table'.format(self.NAME))
      return

    for esedb_record in table.records:
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, table.name, esedb_record,
          value_mappings=self._GUID_TABLE_VALUE_MAPPINGS)

      # TODO: determine if L2ProfileId and L2ProfileFlags are worthwhile to
      # extract.
      event_data = SRUMNetworkDataUsageMonitorEventData()
      event_data.application_identifier = record_values.get('AppId', None)
      event_data.bytes_recieved = record_values.get('BytesRecvd', None)
      event_data.bytes_sent = record_values.get('BytesSent', None)
      event_data.identifier = record_values.get('AutoIncId', None)
      event_data.interface_luid = record_values.get('InterfaceLuid', None)
      event_data.user_identifier = record_values.get('UserId', None)

      timestamp = record_values.get('TimeStamp')
      if timestamp:
        date_time = dfdatetime_ole_automation_date.OLEAutomationDate(
            timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_SAMPLE)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      if not timestamp:
        date_time = dfdatetime_semantic_time.SemanticTime('Not set')
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
        parser_mediator.ProduceEventWithEventData(event, event_data)


esedb.ESEDBParser.RegisterPlugin(SystemResourceUsageMonitorESEDBPlugin)
