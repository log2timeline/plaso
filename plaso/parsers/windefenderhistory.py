# -*- coding: utf-8 -*-
"""Parser for Windows Defender DetectionHistory files."""

from datetime import datetime, timedelta
import os

from dtfabric.runtime import data_maps as dtfabric_data_maps
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events

from plaso.lib import definitions
from plaso.lib import dtfabric_helper
from plaso.lib import errors

from plaso.parsers import interface
from plaso.parsers import manager


class WinDefenderHistoryEventData(events.EventData):
    """Windows Defender Detection History event data."""

    DATA_TYPE = "av:windows:defenderlog"

    def __init__(self):
        """Initializes event data."""
        super(WinDefenderHistoryEventData,
              self).__init__(data_type=self.DATA_TYPE)
        self.sha256 = None
        self.filename = None
        self.extra = None
        self.container_filename = None
        self.web_filename = None
        self.threatname = None
        self.host_and_user = None
        self.process = None


class WinDefenderHistoryParser(interface.FileObjectParser,
                               dtfabric_helper.DtFabricHelper):
    """Parses the Windows Defender History Log."""

    NAME = 'windefenderhistory'

    _FILE_SIGNATURE = "Magic.Version"

    _VALUE_DESCRIPTIONS = [{
        0: 'Threat identifier',
        1: 'Identifier'
    }, {
        0: 'UnknownMagic1',
        1: 'Threat name',
        4: 'Category'
    }, {
        0: 'UnknownMagic2',
        1: 'Resource type',
        2: 'Resource location',
        4: 'Threat tracking data size',
        5: 'Threat tracking data',
        6: 'Last threat status change time',
        12: 'Domain user1',
        14: 'Process name',
        18: 'Initial detection time',
        20: 'Remediation time',
        24: 'Domain user2'
    }]

    _CATEGORY_NAME = {
        0: 'INVALID',
        1: 'ADWARE',
        2: 'SPYWARE',
        3: 'PASSWORDSTEALER',
        4: 'TROJANDOWNLOADER',
        5: 'WORM',
        6: 'BACKDOOR',
        7: 'REMOTEACCESSTROJAN',
        8: 'TROJAN',
        9: 'EMAILFLOODER',
        10: 'KEYLOGGER',
        11: 'DIALER',
        12: 'MONITORINGSOFTWARE',
        13: 'BROWSERMODIFIER',
        14: 'COOKIE',
        15: 'BROWSERPLUGIN',
        16: 'AOLEXPLOIT',
        17: 'NUKER',
        18: 'SECURITYDISABLER',
        19: 'JOKEPROGRAM',
        20: 'HOSTILEACTIVEXCONTROL',
        21: 'SOFTWAREBUNDLER',
        22: 'STEALTHNOTIFIER',
        23: 'SETTINGSMODIFIER',
        24: 'TOOLBAR',
        25: 'REMOTECONTROLSOFTWARE',
        26: 'TROJANFTP',
        27: 'POTENTIALUNWANTEDSOFTWARE',
        28: 'ICQEXPLOIT',
        29: 'TROJANTELNET',
        30: 'EXPLOIT',
        31: 'FILESHARINGPROGRAM',
        32: 'MALWARE_CREATION_TOOL',
        33: 'REMOTE_CONTROL_SOFTWARE',
        34: 'TOOL',
        36: 'TROJAN_DENIALOFSERVICE',
        37: 'TROJAN_DROPPER',
        38: 'TROJAN_MASSMAILER',
        39: 'TROJAN_MONITORINGSOFTWARE',
        40: 'TROJAN_PROXYSERVER',
        42: 'VIRUS',
        43: 'KNOWN',
        44: 'UNKNOWN',
        45: 'SPP',
        46: 'BEHAVIOR',
        47: 'VULNERABILTIY',
        48: 'POLICY',
        49: 'EUS',
        50: 'RANSOM',
        51: 'ASR'
    }

    _DEFINITION_FILE = os.path.join(os.path.dirname(__file__),
                                    'detection_history.yaml')

    def _ReadFileHeader(self, file_object):
        """Reads the file header.

        Args:
            file_object (file): file-like object.

        Raises:
            ParseError: if the file header cannot be read.
        """
        data_type_map = self._GetDataTypeMap('detection_history_value')
        header, header_size = self._ReadStructureFromFileObject(
            file_object, 0, data_type_map)

        data_type_map = self._GetDataTypeMap('detection_history_value')
        _, guid_size = self._ReadStructureFromFileObject(
            file_object, header_size, data_type_map)
        signature, signature_size = self._ReadStructureFromFileObject(
            file_object, header_size + guid_size, data_type_map)

        if (header.data_size != 8 or header.data_type != 8
            ) and self._FILE_SIGNATURE not in signature.value_string:
            raise errors.ParseError('Invalid header')

        return header_size + guid_size + signature_size

    def _ReadThreatTrackingData(self, threat_tracking_data, file_offset):
        """Reads the threat tracking data.
        Args:
            threat_tracking_data (bytes): threat tracking data.
            file_offset (int): offset of the threat tracking data relative to
                the start of the file.
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
            ttv, data_size = self._ReadThreatTrackingValue(
                threat_tracking_data[values_data_offset:],
                file_offset + values_data_offset)
            if hasattr(ttv, 'value_string'):
                threat_tracking[ttv.key_string] = ttv.value_string
            if hasattr(ttv, 'value_integer'):
                threat_tracking[ttv.key_string] = ttv.value_integer
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

        threat_tracking_header = self._ReadStructureFromByteStream(
            threat_tracking_data, 0, data_type_map)

        if threat_tracking_header.header_size > 20:
            # TODO: debug print additional data.
            pass

        return threat_tracking_header

    def _ReadThreatTrackingValue(self, threat_tracking_data, file_offset):
        """Reads the threat tracking value.

        Args:
        threat_tracking_data (bytes): threat tracking data.
        file_offset (int): offset of the threat tracking data relative to
            the start of the file.

        Returns:
        tuple[threat_tracking_value, int]: threat tracking value and data size.

        Raises:
        IOError: if the threat tracking value cannot be read.
        """
        data_type_map = self._GetDataTypeMap('threat_tracking_value')

        context = dtfabric_data_maps.DataTypeMapContext()

        threat_tracking_value = self._ReadStructureFromByteStream(
            threat_tracking_data, file_offset, data_type_map, context=context)

        return threat_tracking_value, context.byte_size

    def _CreateDateTime(self, date_time):
        epoch = timedelta(microseconds=float(date_time / 10))
        dt = datetime(1601, 1, 1) + epoch
        te = dfdatetime_time_elements.TimeElements()
        te.CopyFromDatetime(dt)
        return te

    def _ReadValue(self, file_object, file_offset):
        """Reads the value.
        Args:
        file_object (file): file-like object.
        file_offset (int): offset of the value relative to the start of the file.
        Returns:
        object: value.
        Raises:
        IOError: if the value cannot be read.
        """
        data_type_map = self._GetDataTypeMap('detection_history_value')

        value, _ = self._ReadStructureFromFileObject(file_object, file_offset,
                                                     data_type_map)

        value_object = None
        if value.data_type in (0x00000000, 0x00000005, 0x00000006, 0x00000008):
            value_object = value.value_integer
        elif value.data_type == 0x0000000a:
            value_object = value.value_filetime
        elif value.data_type == 0x00000015:
            value_object = value.value_string
        elif value.data_type == 0x0000001e:
            value_object = value.value_guid
        elif value.data_type == 0x00000028:
            value_object = value.data

        return value_object

    def ParseFileObject(self, parser_mediator, file_object):
        """Parses a Windows Defender History file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
        try:
            file_header_size = self._ReadFileHeader(file_object)
        except (ValueError, errors.ParseError) as e:
            raise errors.WrongParser(
                ('[{0:s}] {1:s} is not a valid Windows Defender History file'
                 ).format(self.NAME, parser_mediator.GetDisplayName()))

        event_data = WinDefenderHistoryEventData()
        threat_attributes = {}
        threat_attributes['Resources'] = []
        value_tuples = []
        temp_resource_name = ""

        file_size = file_object.get_size()
        file_offset = 0
        while file_offset < file_size:
            value_object = self._ReadValue(file_object, file_offset)
            value_tuples.append((file_offset, value_object))
            file_offset = file_object.tell()

        value_index_set = 0
        value_index = 0

        for file_offset, value_object in value_tuples:
            if value_object == 'Magic.Version:1.2':
                if value_index_set < 2:
                    value_index_set += 1
                value_index = 0

            if (value_index_set, value_index) == (2, 5):
                threat_attributes.update(
                    self._ReadThreatTrackingData(value_object,
                                                 file_offset + 8))

            else:
                description = self._VALUE_DESCRIPTIONS[value_index_set].get(
                    value_index,
                    'UNKNOWN_{0:d}_{1:d}'.format(value_index_set, value_index))

                if (value_index_set, value_index) == (1, 4):
                    value_string = '{0!s} ({1:s})'.format(
                        value_object,
                        self._CATEGORY_NAME.get(value_object, 'UNKNOWN'))
                else:
                    value_string = '{0!s}'.format(value_object)

                if description == "Resource type":
                    temp_resource_name = value_string
                elif description == "Resource location" and temp_resource_name is not None:
                    threat_attributes['Resources'].append({
                        'Type':
                        temp_resource_name,
                        'Location':
                        value_string
                    })
                    temp_resource_name = None
                else:
                    threat_attributes[description] = value_string

            value_index += 1

        event_data.threatname = threat_attributes.get('Threat name', 'UNKNOWN')
        filenames = [
            x['Location'] for x in threat_attributes['Resources']
            if x['Type'] == "file"
        ]
        if len(filenames) > 0:
            event_data.filename = filenames[0]
        else:
            event_data.filename = 'UNKNOWN'
            if 'CONTEXT_DATA_FILENAME' in threat_attributes:
                event_data.filename = threat_attributes[
                    'CONTEXT_DATA_FILENAME']
            if 'CONTEXT_DATA_PROCESS_PPID' in threat_attributes:
                event_data.filename += "," + threat_attributes[
                    'CONTEXT_DATA_PROCESS_PPID']
        webfiles = [
            x['Location'] for x in threat_attributes['Resources']
            if x['Type'] == "webfile"
        ]
        if len(webfiles) > 0:
            event_data.web_filename = ", ".join(webfiles)
        containerfiles = [
            x['Location'] for x in threat_attributes['Resources']
            if x['Type'] == "containerfile"
        ]
        if len(containerfiles) > 0:
            event_data.container_filename = ", ".join(containerfiles)
        extrafiles = [
            x['Location'] for x in threat_attributes['Resources']
            if "file" not in x['Type']
        ]
        if len(extrafiles):
            event_data.extra = ", ".join(extrafiles)
        event_data.sha256 = threat_attributes.get('ThreatTrackingSha256',
                                                  'UNKNOWN')
        event_data.host_and_user = threat_attributes.get(
            'Domain user1', 'UNKNOWN')
        event_data.process = threat_attributes.get('Process name', 'Unknown')

        event = time_events.DateTimeValuesEvent(
            self._CreateDateTime(
                threat_attributes.get('ThreatTrackingStartTime', 0)),
            definitions.TIME_DESCRIPTION_RECORDED)

        parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(WinDefenderHistoryParser)
