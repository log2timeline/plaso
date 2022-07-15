# -*- coding: utf-8 -*-
"""Parser for Windows Defender DetectionHistory files."""

from datetime import datetime, timedelta
import os

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
        super(WinDefenderHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
        self.sha256 = None
        self.filename = None
        self.web_filename = None
        self.threatname = None
        self.host_and_user = None
        self.process = None

class WinDefenderHistoryParser(interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
    """Parses the Windows Defender History Log."""

    NAME = 'windefenderhistory'

    _FILE_SIGNATURE = "Magic.Version"

    _DEFINITION_FILE = os.path.join(
        os.path.dirname(__file__), 'windefenderhistory.yml')

    def _ReadFileHeader(self, file_object):
        """Reads the file header.

        Args:
            file_object (file): file-like object.

        Returns:
            file_header: file header.
            file_header_size: file header size.

        Raises:
            ParseError: if the file header cannot be read.
        """
        data_type_map = self._GetDataTypeMap('defender_file_header')

        file_header, file_header_size = self._ReadStructureFromFileObject(
            file_object, 0, data_type_map)

        if self._FILE_SIGNATURE not in file_header.magic_version:
            raise errors.ParseError('Invalid header')

        return (file_header, file_header_size)

    def _CreateDateTime(self, date_time_tuple):
        nanoseconds = int.from_bytes(date_time_tuple, byteorder='little')
        epoch = timedelta(microseconds=float(nanoseconds / 10))
        dt = datetime(1601, 1, 1) + epoch
        te = dfdatetime_time_elements.TimeElements()
        te.CopyFromDatetime(dt)
        return te

    def _ReadBlock(self, file_object, file_offset, extra_offset, map_name):
        data_type_map = self._GetDataTypeMap(map_name)

        return self._ReadStructureFromFileObject(
            file_object, file_offset+extra_offset, data_type_map)

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
            file_header, file_header_size = self._ReadFileHeader(file_object)
        except (ValueError, errors.ParseError) as e:
            raise errors.WrongParser((
                '[{0:s}] {1:s} is not a valid Windows Defender History file').format(
                    self.NAME, parser_mediator.GetDisplayName()))

        size_so_far = file_header_size

        event_data = WinDefenderHistoryEventData()

        threat, threat_size = self._ReadBlock(file_object, size_so_far, 2, 'key_value_pair_with_colon')
        size_so_far += threat_size

        event_data.threatname = threat.value

        _, phb_size = self._ReadBlock(file_object, size_so_far, 0, 'post_header_block')
        size_so_far += phb_size

        file, file_size = self._ReadBlock(file_object, size_so_far, -2, 'file_section')
        size_so_far += file_size

        event_data.filename = file.file_value

        _, pfb_size = self._ReadBlock(file_object, size_so_far, 0, 'post_file_block')
        size_so_far += pfb_size-1

        date_time = None

        while True:
            try:
                tk, tk_size = self._ReadBlock(file_object, size_so_far, 0, 'kv_block_key')
                if tk.key == '':
                    break
                size_so_far += tk_size
                if tk.value_type == 6:
                    tv, tv_size = self._ReadBlock(file_object, size_so_far, 0, 'kv_block_string_value')
                    size_so_far += tv_size
                    if "Sha256" in tk.key:
                        event_data.sha256 = tv.value.rstrip('\x00')
                elif tk.value_type == 3: # Flag
                    tv, tv_size = self._ReadBlock(file_object, size_so_far, 0, 'kv_block_flags_value')
                    size_so_far += tv_size
                elif tk.value_type == 5: # Bool
                    size_so_far += 1
                    continue
                elif tk.value_type == 4: # Date Time
                    tv, tv_size = self._ReadBlock(file_object, size_so_far, 0, 'kv_block_bytes_value')
                    size_so_far += tv_size
                    if "Time" in tk.key:
                        date_time = tv.value # Int tuple
                else: # Catch all
                    tv, tv_size = self._ReadBlock(file_object, size_so_far, 0, 'kv_block_bytes_value')
                    size_so_far += tv_size
            except errors.ParseError:
                break

        backup_size = size_so_far
        try:
            _, phb_size = self._ReadBlock(file_object, size_so_far, -1, 'post_header_block')
            size_so_far += phb_size

            file, file_size = self._ReadBlock(file_object, size_so_far, -3, 'file_section')
            size_so_far += file_size
            event_data.web_filename = file.file_value
        except errors.ParseError:
            size_so_far = backup_size

        _, pkvb_size = self._ReadBlock(file_object, size_so_far, 0,
                                       'post_kv_block')
        size_so_far += pkvb_size + 2

        u, _ = self._ReadBlock(file_object, size_so_far, 1, 'user_and_process')

        event_data.host_and_user = u.user
        event_data.process = u.process

        event = time_events.DateTimeValuesEvent(
            self._CreateDateTime(date_time),
            definitions.TIME_DESCRIPTION_RECORDED)
        parser_mediator.ProduceEventWithEventData(event, event_data)

manager.ParsersManager.RegisterParser(WinDefenderHistoryParser)
