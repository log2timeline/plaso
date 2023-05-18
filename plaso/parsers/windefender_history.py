# -*- coding: utf-8 -*-
"""Parser for Windows Defender scan DetectionHistory files."""

import os

from dfdatetime import filetime as dfdatetime_filetime

from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class WindowsDefenderHistoryEventData(events.EventData):
  """Windows Defender scan DetectionHistory event data.

  Attributes:
    additional_filenames (list[str]): locations of additional detected files.
    container_filenames (list[str]): location of files detected inside a
        container.
    filename (str): name of the file that the threat was detected in.
    host_and_user (str): name of the host and user in "DOMAIN\\USER" format.
    process (str): name of the process that caused the detection.
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
    sha256 (str): SHA-256 hash of the file.
    threat_name (str): name of the threat that was detected.
    web_filenames (list[str]): URI of files detected as downloaded from the web.
  """

  DATA_TYPE = 'av:defender:detection_history'

  def __init__(self):
    """Initializes event data."""
    super(WindowsDefenderHistoryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.additional_filenames = None
    self.container_filenames = None
    self.filename = None
    self.host_and_user = None
    self.recorded_time = None
    self.process = None
    self.sha256 = None
    self.threat_name = None
    self.web_filenames = None


class WinDefenderHistoryParser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parses a Windows Defender scan DetectionHistory file."""

  NAME = 'windefender_history'
  DATA_FORMAT = 'Windows Defender scan DetectionHistory file'

  _FILE_SIGNATURE = 'Magic.Version:1.2'

  _VALUE_DESCRIPTIONS = [
      {0: 'Threat identifier', 1: 'Identifier'},
      {0: 'UnknownMagic1', 1: 'Threat name', 4: 'Category'},
      {0: 'UnknownMagic2',
       1: 'Resource type',
       2: 'Resource location',
       4: 'Threat tracking data size',
       5: 'Threat tracking data',
       6: 'Last threat status change time',
       12: 'Domain user1',
       14: 'Process name',
       18: 'Initial detection time',
       20: 'Remediation time',
       24: 'Domain user2'}]

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'windefender_history.yaml')

  _VALUE_DATA_TYPE_BINARY_DATA = 0x00000028
  _VALUE_DATA_TYPE_FILETIME = 0x0000000a
  _VALUE_DATA_TYPE_GUID = 0x0000001e
  _VALUE_DATA_TYPE_STRING = 0x00000015

  _VALUE_DATA_TYPES_INTEGER = frozenset([
      0x00000000, 0x00000005, 0x00000006, 0x00000008])

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(
        cls._FILE_SIGNATURE.encode('utf-16-le'), offset=0x30)
    return format_specification

  def _ReadThreatTrackingData(self, threat_tracking_data, file_offset):
    """Reads the threat tracking data.

    Args:
      threat_tracking_data (bytes): threat tracking data.
      file_offset (int): offset of the threat tracking data relative to
          the start of the file.

    Returns:
      dict[str, str]: Mapping of threat tracking keys to values.

    Raises:
      IOError: if the threat tracking data cannot be read.
    """
    threat_tracking = {}
    data_type_map = self._GetDataTypeMap('uint32le')

    values_data_size = self._ReadStructureFromByteStream(
        threat_tracking_data, 0, data_type_map)

    if values_data_size != 1:
      values_data_offset = 4
      values_data_end_offset = values_data_size
    else:
      header = self._ReadThreatTrackingHeader(threat_tracking_data)

    values_data_offset = header.header_size + 4
    values_data_end_offset = header.total_data_size

    while values_data_offset < values_data_end_offset:
      threat_value, data_size = self._ReadThreatTrackingValue(
          threat_tracking_data[values_data_offset:],
          file_offset + values_data_offset)
      if hasattr(threat_value, 'value_string'):
        threat_tracking[threat_value.key_string] = threat_value.value_string
      if hasattr(threat_value, 'value_integer'):
        threat_tracking[threat_value.key_string] = threat_value.value_integer
      values_data_offset += data_size

    return threat_tracking

  def _ReadThreatTrackingHeader(self, threat_tracking_data):
    """Reads the threat tracking header.

    Args:
      threat_tracking_data (bytes): threat tracking data.

    Returns:
      threat_tracking_header: threat tracking header.

    Raises:
      IOError: if the threat tracking header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('threat_tracking_header')

    return self._ReadStructureFromByteStream(
        threat_tracking_data, 0, data_type_map)

  def _ReadThreatTrackingValue(self, threat_tracking_data, file_offset):
    """Reads the threat tracking value.

    Args:
      threat_tracking_data (bytes): threat tracking data.
      file_offset (int): offset of the threat tracking data relative to
          the start of the file.

    Returns:
      tuple[threat_tracking_value, int]: threat tracking value and
          data size.

    Raises:
      IOError: if the threat tracking value cannot be read.
    """
    data_type_map = self._GetDataTypeMap('threat_tracking_value')

    context = dtfabric_data_maps.DataTypeMapContext()

    threat_tracking_value = self._ReadStructureFromByteStream(
        threat_tracking_data, file_offset, data_type_map, context=context)

    return threat_tracking_value, context.byte_size

  def _ReadValue(self, file_object, file_offset, parser_mediator):
    """Reads the value.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the value relative to the start of the file.
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.

    Returns:
      object: value.

    Raises:
      IOError: if the value cannot be read.
      ParseError: when the value data type is unknown.
    """
    data_type_map = self._GetDataTypeMap('detection_history_value')

    value, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    value_object = None
    if value.data_type in self._VALUE_DATA_TYPES_INTEGER:
      value_object = value.value_integer
    elif value.data_type == self._VALUE_DATA_TYPE_FILETIME:
      value_object = value.value_filetime
    elif value.data_type == self._VALUE_DATA_TYPE_STRING:
      value_object = value.value_string
    elif value.data_type == self._VALUE_DATA_TYPE_GUID:
      value_object = value.value_guid
    elif value.data_type == self._VALUE_DATA_TYPE_BINARY_DATA:
      value_object = value.data
    else:
      parser_mediator.ProduceExtractionWarning(
          'unknown value data type: {0!s}'.format(value.data_type))
      value_object = value.data

    return value_object

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows Defender History file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
            parsers and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    value_tuples = []

    file_offset = 0
    file_size = file_object.get_size()

    while file_offset < file_size:
      value_object = self._ReadValue(file_object, file_offset, parser_mediator)
      value_tuples.append((file_offset, value_object))
      file_offset = file_object.tell()

    resource_name = ''
    threat_attributes = {'Resources': []}
    value_index_set = 0
    value_index = 0

    for file_offset, value_object in value_tuples:
      if value_object == self._FILE_SIGNATURE:
        if value_index_set < 2:
          value_index_set += 1
        value_index = 0

      if (value_index_set, value_index) == (2, 5):
        threat_attributes.update(
            self._ReadThreatTrackingData(value_object, file_offset + 8))

      else:
        description = self._VALUE_DESCRIPTIONS[value_index_set].get(
            value_index, 'UNKNOWN_{0:d}_{1:d}'.format(
                value_index_set, value_index))

        value_string = '{0!s}'.format(value_object)

        if description == 'Resource type':
          resource_name = value_string

        elif description == 'Resource location' and resource_name is not None:
          threat_attributes['Resources'].append(
              {'Type': resource_name, 'Location': value_string})
          resource_name = None

        else:
          threat_attributes[description] = value_string

      value_index += 1

    filenames = [
        threat_attribute['Location']
        for threat_attribute in threat_attributes['Resources']
        if threat_attribute['Type'] == 'file']

    if not filenames:
      filename = threat_attributes.get('CONTEXT_DATA_FILENAME', None)
      process_ppid = threat_attributes.get('CONTEXT_DATA_PROCESS_PPID', None)

      filenames = [','.join(list(filter(None, [filename, process_ppid])))]

    web_files = [
        threat_attribute['Location']
        for threat_attribute in threat_attributes['Resources']
        if threat_attribute['Type'] == 'webfile']

    container_files = [
        threat_attribute['Location']
        for threat_attribute in threat_attributes['Resources']
        if threat_attribute['Type'] == 'containerfile']

    additional_filenames = [
        threat_attribute['Location']
        for threat_attribute in threat_attributes['Resources']
        if 'file' not in threat_attribute['Type']]

    timestamp = threat_attributes.get('ThreatTrackingStartTime', 0)

    event_data = WindowsDefenderHistoryEventData()
    event_data.additional_filenames = additional_filenames
    event_data.container_filenames = container_files
    event_data.filename = filenames[0]
    event_data.host_and_user = threat_attributes.get('Domain user1', None)
    event_data.process = threat_attributes.get('Process name', None)
    event_data.recorded_time = dfdatetime_filetime.Filetime(
        timestamp=timestamp)
    event_data.sha256 = threat_attributes.get('ThreatTrackingSha256', None)
    event_data.threat_name = threat_attributes.get('Threat name', None)
    event_data.web_filenames = web_files

    parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(WinDefenderHistoryParser)
