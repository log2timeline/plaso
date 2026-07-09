"""Parser for Systemd journal files."""

import lzma
import os

from dfdatetime import posix_time as dfdatetime_posix_time

from lz4 import block as lz4_block
import zstd

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class SystemdJournalEventData(events.EventData):
    """Systemd journal event data.

    Attributes:
      audit_login_identifier (str): login user identifier (audit loginuid) of the
          process that logged the entry.
      boot_identifier (str): identifier of the boot the entry was logged in.
      command_line (str): command line of the process that logged the entry.
      executable (str): path of the executable of the process that logged the entry.
      facility (str): syslog facility.
      group_identifier (int): group identifier (GID) of the process that logged the
          entry.
      hostname (str): hostname.
      machine_identifier (str): identifier of the machine the entry was logged on.
      message_body (str): message body.
      pid (int): process identifier (PID).
      process_name (str): name of the process that logged the entry.
      recorded_time (dfdatetime.DateTimeValues): date and time the log entry was
          recorded (received) by journald on the originating host.
      reporter (str): reporter.
      selinux_context (str): SELinux security context of the process that logged the
          entry.
      severity (int): syslog severity.
      systemd_unit (str): systemd unit of the process that logged the entry.
      transport (str): how the entry was received by the journal.
      user_identifier (int): user identifier (UID) of the process that logged the entry.
      written_time (dfdatetime.DateTimeValues): date and time the log entry was written.
    """

    DATA_TYPE = "systemd:journal"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.audit_login_identifier = None
        self.boot_identifier = None
        self.command_line = None
        self.executable = None
        self.facility = None
        self.group_identifier = None
        self.hostname = None
        self.machine_identifier = None
        self.message_body = None
        self.pid = None
        self.process_name = None
        self.recorded_time = None
        self.reporter = None
        self.selinux_context = None
        self.severity = None
        self.systemd_unit = None
        self.transport = None
        self.user_identifier = None
        self.written_time = None


class SystemdJournalParser(interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
    """Parses Systemd Journal files."""

    NAME = "systemd_journal"
    DATA_FORMAT = "Systemd journal file"

    _DEFINITION_FILE = os.path.join(os.path.dirname(__file__), "systemd_journal.yaml")

    _OBJECT_COMPRESSED_FLAG_XZ = 1
    _OBJECT_COMPRESSED_FLAG_LZ4 = 2
    _OBJECT_COMPRESSED_FLAG_ZSTD = 4

    _OBJECT_TYPE_UNUSED = 0
    _OBJECT_TYPE_DATA = 1
    _OBJECT_TYPE_FIELD = 2
    _OBJECT_TYPE_ENTRY = 3
    _OBJECT_TYPE_DATA_HASH_TABLE = 4
    _OBJECT_TYPE_FIELD_HASH_TABLE = 5
    _OBJECT_TYPE_ENTRY_ARRAY = 6
    _OBJECT_TYPE_TAG = 7

    _HEADER_SIZE_PRE_VERSION_187 = 208
    _HEADER_SIZE_VERSION_187 = 224
    _HEADER_SIZE_VERSION_189 = 240
    _HEADER_SIZE_VERSION_246 = 256
    _HEADER_SIZE_VERSION_252 = 264
    _HEADER_SIZE_VERSION_254 = 272

    _SUPPORTED_FILE_HEADER_SIZES = frozenset(
        [
            _HEADER_SIZE_PRE_VERSION_187,
            _HEADER_SIZE_VERSION_187,
            _HEADER_SIZE_VERSION_189,
            _HEADER_SIZE_VERSION_246,
            _HEADER_SIZE_VERSION_252,
            _HEADER_SIZE_VERSION_254,
        ]
    )

    _HEADER_INCOMPATIBLE_COMPACT = 16

    _INTEGER_FIELDS = (
        "_GID",
        "_PID",
        "_SOURCE_REALTIME_TIMESTAMP",
        "_UID",
        "PRIORITY",
        "SYSLOG_PID",
    )

    _SYSLOG_FACILITIES = {
        0: "kernel message",
        1: "user-level message",
        2: "mail system",
        3: "system daemons",
        4: "security/authorization messages",
        5: "messages generated internally by syslogd",
        6: "line printer subsystem",
        7: "network news subsystem",
        8: "UUCP subsystem",
        9: "clock daemon",
        10: "security/authorization messages",
        11: "FTP daemon",
        12: "NTP subsystem",
        13: "log audit",
        14: "log alert",
        15: "clock daemon",
        16: "local use 0",
        17: "local use 1",
        18: "local use 2",
        19: "local use 3",
        20: "local use 4",
        21: "local use 5",
        22: "local use 6",
        23: "local use 7",
    }

    def __init__(self):
        """Initializes a parser."""
        super().__init__()
        self._maximum_journal_file_offset = 0
        self._is_compact = False

    def _ParseDataObject(self, file_object, file_offset):
        """Parses a data object.

        Args:
          file_object (dfvfs.FileIO): a file-like object.
          file_offset (int): offset of the data object relative to the start
              of the file-like object.

        Returns:
          bytes: data.

        Raises:
          ParseError: if the data object cannot be parsed.
        """
        if self._is_compact:
            data_object_map = self._GetDataTypeMap(
                "systemd_journal_data_object_compact"
            )
        else:
            data_object_map = self._GetDataTypeMap("systemd_journal_data_object")

        try:
            data_object, data_object_header_size = self._ReadStructureFromFileObject(
                file_object, file_offset, data_object_map
            )
        except (ValueError, errors.ParseError) as exception:
            raise errors.ParseError(
                f"Unable to parse data object at offset: 0x{file_offset:08x} "
                f"with error: {exception!s}"
            )

        if data_object.object_type != self._OBJECT_TYPE_DATA:
            raise errors.ParseError(
                f"Unsupported object type: {data_object.object_type:d}"
            )

        if data_object.object_flags not in (
            0,
            self._OBJECT_COMPRESSED_FLAG_XZ,
            self._OBJECT_COMPRESSED_FLAG_LZ4,
            self._OBJECT_COMPRESSED_FLAG_ZSTD,
        ):
            raise errors.ParseError(
                f"Unsupported object flags: 0x{data_object.object_flags:02x}"
            )

        # The data is read separately for performance reasons.
        data_offset = file_offset + data_object_header_size
        data_size = data_object.data_size - data_object_header_size
        data = file_object.read(data_size)

        if data_object.object_flags & self._OBJECT_COMPRESSED_FLAG_XZ:
            try:
                data = lzma.decompress(data)
            except (EOFError, lzma.LZMAError) as exception:
                raise errors.ParseError(
                    f"Unable to decompress XZ at offset: 0x{data_offset:08x} with "
                    f"error: {exception!s}"
                )

        elif data_object.object_flags & self._OBJECT_COMPRESSED_FLAG_LZ4:
            uncompressed_size_map = self._GetDataTypeMap("uint32le")

            try:
                uncompressed_size = self._ReadStructureFromByteStream(
                    data, data_offset, uncompressed_size_map
                )
            except (ValueError, errors.ParseError) as exception:
                raise errors.ParseError(
                    f"Unable to parse LZ4 uncompressed size at offset: "
                    f"0x{data_offset:08x} with error: {exception!s}"
                )

            try:
                data = lz4_block.decompress(
                    data[8:], uncompressed_size=uncompressed_size
                )
            except (ValueError, lz4_block.LZ4BlockError) as exception:
                raise errors.ParseError(
                    f"Unable to decompress LZ4 at offset: 0x{data_offset:08x} with "
                    f"error: {exception!s}"
                )

        elif data_object.object_flags & self._OBJECT_COMPRESSED_FLAG_ZSTD:
            try:
                data = zstd.decompress(data)
            except zstd.Error as exception:
                raise errors.ParseError(
                    f"Unable to decompress ZSTD at offset: 0x{data_offset:08x} with "
                    f"error: {exception!s}"
                )

        return data

    def _ParseEntryArrayObject(self, file_object, file_offset):
        """Parses an entry array object.

        Args:
          file_object (dfvfs.FileIO): a file-like object.
          file_offset (int): offset of the entry array object relative to the start
              of the file-like object.

        Returns:
          systemd_journal_entry_array_object: entry array object.

        Raises:
          ParseError: if the entry array object cannot be parsed.
        """
        if self._is_compact:
            entry_array_object_map = self._GetDataTypeMap(
                "systemd_journal_entry_array_object_compact"
            )
        else:
            entry_array_object_map = self._GetDataTypeMap(
                "systemd_journal_entry_array_object"
            )

        try:
            entry_array_object, _ = self._ReadStructureFromFileObject(
                file_object, file_offset, entry_array_object_map
            )
        except (ValueError, errors.ParseError) as exception:
            raise errors.ParseError(
                f"Unable to parse entry array object at offset: 0x{file_offset:08x} "
                f"with error: {exception!s}"
            )

        if entry_array_object.object_type != self._OBJECT_TYPE_ENTRY_ARRAY:
            raise errors.ParseError(
                f"Unsupported object type: {entry_array_object.object_type:d}"
            )

        if entry_array_object.object_flags != 0:
            raise errors.ParseError(
                f"Unsupported object flags: 0x{entry_array_object.object_flags:02x}"
            )

        return entry_array_object

    def _ParseEntryObject(self, file_object, file_offset):
        """Parses an entry object.

        Args:
          file_object (dfvfs.FileIO): a file-like object.
          file_offset (int): offset of the entry object relative to the start
              of the file-like object.

        Returns:
          systemd_journal_entry_object: entry object.

        Raises:
          ParseError: if the entry object cannot be parsed.
        """
        entry_object_map = self._GetDataTypeMap("systemd_journal_entry_object")

        try:
            entry_object, _ = self._ReadStructureFromFileObject(
                file_object, file_offset, entry_object_map
            )
        except (ValueError, errors.ParseError) as exception:
            raise errors.ParseError(
                f"Unable to parse entry object at offset: 0x{file_offset:08x} "
                f"with error: {exception!s}"
            )

        if entry_object.object_type != self._OBJECT_TYPE_ENTRY:
            raise errors.ParseError(
                f"Unsupported object type: {entry_object.object_type:d}"
            )

        if entry_object.object_flags != 0:
            raise errors.ParseError(
                f"Unsupported object flags: 0x{entry_object.object_flags:02x}"
            )

        return entry_object

    def _ParseEntryObjectOffsets(self, file_object, file_offset):
        """Parses entry array objects for the offset of the entry objects.

        Args:
          file_object (dfvfs.FileIO): a file-like object.
          file_offset (int): offset of the first entry array object relative to
              the start of the file-like object.

        Returns:
          list[int]: offsets of the entry objects.
        """
        entry_array_object = self._ParseEntryArrayObject(file_object, file_offset)

        entry_object_offsets = list(entry_array_object.entry_object_offsets)
        while entry_array_object.next_entry_array_offset != 0:
            entry_array_object = self._ParseEntryArrayObject(
                file_object, entry_array_object.next_entry_array_offset
            )
            entry_object_offsets.extend(entry_array_object.entry_object_offsets)

        return entry_object_offsets

    def _ParseKeyValuePair(self, parser_mediator, field_data):
        """Parses a key value pair.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          field_data (bytes): journal field data, which is "key=value" where the
              value can contain arbitrary binary (non-UTF-8) data.

        Returns:
          tuple: containing:

              str: key decoded as UTF-8.
              object: value decoded as UTF-8.
              bool: value to indicate the key value pair was corrupted.
        """
        key_data, _, value_data = field_data.partition(b"=")
        corrupted = False

        try:
            key = key_data.decode("utf-8")
        except UnicodeDecodeError:
            parser_mediator.ProduceWarning(
                "Unable to decode journal field key as UTF-8. Unsupported code points "
                "are escaped."
            )
            key = key_data.decode("utf-8", errors="backslashreplace")
            corrupted = True

        if not value_data:
            value = None
        else:
            try:
                value = value_data.decode("utf-8")
            except UnicodeDecodeError:
                parser_mediator.ProduceWarning(
                    f"Unable to decode journal field with key: {key:s} value as UTF-8. "
                    f"Unsupported code points are escaped."
                )
                value = value_data.decode("utf-8", errors="backslashreplace")
                corrupted = True

        if value is not None and not corrupted and key in self._INTEGER_FIELDS:
            try:
                value = int(value, 10)
            except ValueError:
                parser_mediator.ProduceWarning(
                    f"Unsupported {key:s} integer value: '{value:s}'"
                )
                corrupted = True

        return key, value, corrupted

    def _ParseJournalEntry(self, parser_mediator, file_object, file_offset):
        """Parses a journal entry.

        This method will generate an event per ENTRY object.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): a file-like object.
          file_offset (int): offset of the entry object relative to the start
              of the file-like object.

        Returns:
          tuple: containing:

              dict[str, objects]: fields in the journal entry.
              bool: True if the journal entry was corrupted.

        Raises:
          ParseError: when an object offset is out of bounds.
        """
        entry_object = self._ParseEntryObject(file_object, file_offset)

        # The data is read separately for performance reasons.
        if self._is_compact:
            entry_item_map = self._GetDataTypeMap("systemd_journal_entry_item_compact")
        else:
            entry_item_map = self._GetDataTypeMap("systemd_journal_entry_item")

        file_offset += 64
        data_end_offset = file_offset + entry_object.data_size - 64

        fields = {"real_time": entry_object.real_time}
        corrupted = False

        while file_offset < data_end_offset:
            try:
                entry_item, entry_item_data_size = self._ReadStructureFromFileObject(
                    file_object, file_offset, entry_item_map
                )
            except (ValueError, errors.ParseError) as exception:
                raise errors.ParseError(
                    f"Unable to parse entry item at offset: 0x{file_offset:08x} with "
                    f"error: {exception!s}"
                )

            file_offset += entry_item_data_size

            if entry_item.object_offset < self._maximum_journal_file_offset:
                raise errors.ParseError(
                    f"object offset should be after hash tables "
                    f"({entry_item.object_offset:d} < "
                    f"{self._maximum_journal_file_offset:d})"
                )

            field_data = self._ParseDataObject(file_object, entry_item.object_offset)
            key, value, value_corrupted = self._ParseKeyValuePair(
                parser_mediator, field_data
            )
            fields[key] = value
            corrupted = corrupted or value_corrupted

        return fields, corrupted

    @classmethod
    def GetFormatSpecification(cls):
        """Retrieves the format specification.

        Returns:
          FormatSpecification: format specification.
        """
        format_specification = specification.FormatSpecification(cls.NAME)
        format_specification.AddNewSignature(b"LPKSHHRH", offset=0)
        return format_specification

    def ParseFileObject(self, parser_mediator, file_object):
        """Parses a Systemd journal file-like object.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): a file-like object.

        Raises:
          WrongParser: when the header cannot be parsed.
        """
        file_header_map = self._GetDataTypeMap("systemd_journal_file_header")

        try:
            file_header, _ = self._ReadStructureFromFileObject(
                file_object, 0, file_header_map
            )
        except (ValueError, errors.ParseError) as exception:
            raise errors.WrongParser(
                f"Unable to parse file header with error: {exception!s}"
            )

        if file_header.header_size not in self._SUPPORTED_FILE_HEADER_SIZES:
            raise errors.WrongParser(
                f"Unsupported file header size: {file_header.header_size:d}"
            )

        if file_header.incompatible_flags & self._HEADER_INCOMPATIBLE_COMPACT:
            self._is_compact = True

        data_hash_table_end_offset = (
            file_header.data_hash_table_offset + file_header.data_hash_table_size
        )
        field_hash_table_end_offset = (
            file_header.field_hash_table_offset + file_header.field_hash_table_size
        )
        self._maximum_journal_file_offset = max(
            data_hash_table_end_offset, field_hash_table_end_offset
        )
        entry_object_offsets = self._ParseEntryObjectOffsets(
            file_object, file_header.entry_array_offset
        )
        for entry_object_offset in entry_object_offsets:
            if entry_object_offset == 0:
                continue

            try:
                fields, corrupted = self._ParseJournalEntry(
                    parser_mediator, file_object, entry_object_offset
                )
            except errors.ParseError as exception:
                parser_mediator.ProduceWarning(
                    f"Unable to parse journal entry at offset: "
                    f"0x{entry_object_offset:08x} with error: {exception!s}"
                )
                continue

            date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
                timestamp=fields["real_time"]
            )
            event_data = SystemdJournalEventData()

            # The SYSLOG_FACILITY values can contain either a string e.g. "DHCP4" or an
            # integer that maps to a predefined facility.
            facility = fields.get("SYSLOG_FACILITY")
            if facility is not None:
                try:
                    facility_numeric = int(facility, 10)
                    facility = self._SYSLOG_FACILITIES.get(facility_numeric, facility)
                except ValueError:
                    pass

            event_data.audit_login_identifier = fields.get("_AUDIT_LOGINUID")
            event_data.boot_identifier = fields.get("_BOOT_ID")
            event_data.command_line = fields.get("_CMDLINE")
            event_data.executable = fields.get("_EXE")
            event_data.facility = facility
            event_data.group_identifier = fields.get("_GID")
            event_data.hostname = fields.get("_HOSTNAME")
            event_data.machine_identifier = fields.get("_MACHINE_ID")
            event_data.message_body = fields.get("MESSAGE")
            event_data.process_name = fields.get("_COMM")
            # Fall back to the _COMM when SYSLOG_IDENTIFIER is absent.
            event_data.reporter = fields.get("SYSLOG_IDENTIFIER") or fields.get("_COMM")
            event_data.selinux_context = fields.get("_SELINUX_CONTEXT")
            event_data.severity = fields.get("PRIORITY")
            event_data.systemd_unit = fields.get("_SYSTEMD_UNIT")
            event_data.transport = fields.get("_TRANSPORT")
            event_data.user_identifier = fields.get("_UID")
            event_data.written_time = date_time

            # _SOURCE_REALTIME_TIMESTAMP is the earliest trusted (event) time of
            # the message on the originating host, whereas written_time
            # (__REALTIME_TIMESTAMP) is journald's reception time; for journals
            # relayed via systemd-journal-remote the latter is the collection
            # time on the central host, so the two diverge. It is a trusted
            # field and should be numeric microseconds, so a malformed value is
            # surfaced rather than dropped.
            source_realtime = fields.get("_SOURCE_REALTIME_TIMESTAMP")
            if source_realtime is not None:
                event_data.recorded_time = (
                    dfdatetime_posix_time.PosixTimeInMicroseconds(
                        timestamp=source_realtime
                    )
                )

            if event_data.reporter and event_data.reporter != "kernel":
                event_data.pid = fields.get("_PID", fields.get("SYSLOG_PID"))

            parser_mediator.ProduceEventData(event_data, corrupted=corrupted)


manager.ParsersManager.RegisterParser(SystemdJournalParser)
