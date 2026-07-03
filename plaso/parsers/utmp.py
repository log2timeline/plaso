"""Parser for Linux utmp files."""

import os

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import definitions
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class UtmpEventData(events.EventData):
    """Linux libc6 utmp event data.

    Attributes:
      exit_status (int): exit status.
      hostname (str): hostname or IP address.
      ip_address (str): IP address from the connection.
      offset (int): offset of the utmp record relative to the start of the file,
          from which the event data was extracted.
      pid (int): process identifier (PID).
      terminal_identifier (int): inittab identifier.
      terminal (str): type of terminal.
      type (int): type of login.
      username (str): user name.
      written_time (dfdatetime.DateTimeValues): entry written date and time.
    """

    DATA_TYPE = "linux:utmp:event"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.exit_status = None
        self.hostname = None
        self.ip_address = None
        self.offset = None
        self.pid = None
        self.terminal_identifier = None
        self.terminal = None
        self.type = None
        self.username = None
        self.written_time = None


class UtmpParser(interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
    """Parser for Linux libc6 utmp files."""

    NAME = "utmp"
    DATA_FORMAT = "Linux libc6 utmp file"

    _DEFINITION_FILE = os.path.join(os.path.dirname(__file__), "utmp.yaml")

    _EMPTY_IP_ADDRESS = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    _SUPPORTED_TYPES = frozenset(range(0, 10))

    _INIT_PROCESS_TYPE = 5
    _DEAD_PROCESS_TYPE = 8

    # A libc6 utmp record is a fixed-size structure: 384 bytes for the 32-bit
    # layout and 400 bytes for the 64-bit layout (e.g. aarch64).
    _ENTRY_SIZE_32BIT = 384
    _ENTRY_SIZE_64BIT = 400

    def _ReadEntry(self, parser_mediator, file_object, file_offset, entry_map):
        """Reads an utmp entry.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): a file-like object.
          file_offset (int): offset of the data relative to the start of
              the file-like object.
          entry_map (dtfabric.DataTypeMap): data type map of the utmp entry.

        Returns:
          tuple: containing:

            UtmpEventData: event data of the utmp entry read.
            list[str]: warning messages emitted by the parser.

        Raises:
          ParseError: if the entry cannot be parsed.
        """
        warning_strings = []

        try:
            entry, _ = self._ReadStructureFromFileObject(
                file_object, file_offset, entry_map
            )
        except (ValueError, errors.ParseError) as exception:
            raise errors.ParseError(
                (
                    f"Unable to parse utmp entry at offset: 0x{file_offset:08x} with "
                    f"error: {exception!s}."
                )
            )

        if entry.type not in self._SUPPORTED_TYPES:
            raise errors.ParseError(f"Unsupported type: {entry.type:d}")

        code_page = parser_mediator.GetCodePage()

        try:
            username = entry.username.split(b"\x00")[0]
            username = username.decode(code_page).rstrip()
        except UnicodeDecodeError:
            warning_strings.append("unable to decode username string")
            username = None

        try:
            terminal = entry.terminal.split(b"\x00")[0]
            terminal = terminal.decode(code_page).rstrip()
        except UnicodeDecodeError:
            warning_strings.append("unable to decode terminal string")
            terminal = None

        if terminal == "~":
            terminal = "system boot"

        try:
            hostname = entry.hostname.split(b"\x00")[0]
            hostname = hostname.decode(code_page).rstrip()
        except UnicodeDecodeError:
            warning_strings.append("unable to decode hostname string")
            hostname = None

        if not hostname or hostname == ":0":
            hostname = "localhost"

        if entry.ip_address[4:] == self._EMPTY_IP_ADDRESS[4:]:
            ip_address = self._FormatPackedIPv4Address(entry.ip_address[:4])
        else:
            ip_address = self._FormatPackedIPv6Address(entry.ip_address)

        timestamp = entry.microseconds + (
            entry.timestamp * definitions.MICROSECONDS_PER_SECOND
        )

        # TODO: add termination status.
        event_data = UtmpEventData()
        event_data.hostname = hostname
        event_data.exit_status = entry.exit_status
        event_data.ip_address = ip_address
        event_data.offset = file_offset
        event_data.pid = entry.pid
        event_data.terminal = terminal or None
        event_data.terminal_identifier = entry.terminal_identifier
        event_data.type = entry.type
        event_data.username = username or None
        event_data.written_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=timestamp
        )

        return event_data, warning_strings

    def _IsValidFirstEntry(self, file_object, entry_map):
        """Checks whether the first record is a valid utmp entry for a layout.

        Used to tell the 32-bit and 64-bit record layouts apart. The subsecond
        (microseconds) field is defined to be less than 1,000,000; a record read
        with the wrong layout has the wider seconds field spill into it, so a
        value outside that range indicates the layout is incorrect.

        Args:
          file_object (dfvfs.FileIO): a file-like object.
          entry_map (dtfabric.DataTypeMap): candidate utmp entry data type map.

        Returns:
          bool: True if the first record is a valid utmp entry.
        """
        try:
            entry, _ = self._ReadStructureFromFileObject(file_object, 0, entry_map)
        except (ValueError, errors.ParseError):
            return False

        return entry.type in self._SUPPORTED_TYPES and 0 <= entry.microseconds < 1000000

    def _GetEntryFormat(self, file_object, file_size):
        """Determines the utmp record size and data type map for a file.

        A libc6 utmp file is an array of fixed-size records: 384 bytes for the
        32-bit layout or 400 bytes for the 64-bit layout (e.g. aarch64, where the
        session and timeval fields are wider). The layout selected is the one
        whose first record is valid. The 32-bit layout is checked first: a 64-bit
        record read as 32-bit is reliably rejected (its seconds field spills into
        the subsecond field), whereas a 32-bit record read as 64-bit can look
        valid; see _IsValidFirstEntry.

        Args:
          file_object (dfvfs.FileIO): a file-like object.
          file_size (int): size of the file-like object.

        Returns:
          tuple[int, dtfabric.DataTypeMap]: utmp record size and data type map.
        """
        for entry_size, definition_name in (
            (self._ENTRY_SIZE_32BIT, "linux_libc6_utmp_entry"),
            (self._ENTRY_SIZE_64BIT, "linux_libc6_utmp_entry_64bit"),
        ):
            if file_size < entry_size:
                continue
            entry_map = self._GetDataTypeMap(definition_name)
            if self._IsValidFirstEntry(file_object, entry_map):
                return entry_size, entry_map

        return self._ENTRY_SIZE_32BIT, self._GetDataTypeMap("linux_libc6_utmp_entry")

    def ParseFileObject(self, parser_mediator, file_object):
        """Parses an utmp file-like object.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): a file-like object.

        Raises:
          WrongParser: when the file cannot be parsed.
        """
        file_size = file_object.get_size()
        entry_size, entry_map = self._GetEntryFormat(file_object, file_size)

        file_offset = 0

        try:
            event_data, warning_strings = self._ReadEntry(
                parser_mediator, file_object, file_offset, entry_map
            )
        except errors.ParseError as exception:
            raise errors.WrongParser(
                f"Unable to parse first utmp entry with error: {exception!s}"
            )

        if not event_data.written_time:
            raise errors.WrongParser(
                "Unable to parse first utmp entry with error: missing written time"
            )

        if not event_data.username and event_data.type not in (
            self._DEAD_PROCESS_TYPE,
            self._INIT_PROCESS_TYPE,
        ):
            raise errors.WrongParser(
                "Unable to parse first utmp entry with error: missing username"
            )

        if warning_strings:
            all_warnings = ", ".join(warning_strings)
            raise errors.WrongParser(
                f"Unable to parse first utmp entry with error: {all_warnings:s}"
            )

        parser_mediator.ProduceEventData(event_data)

        file_offset = file_object.tell()

        while file_offset < file_size:
            if parser_mediator.abort:
                break

            try:
                event_data, warning_strings = self._ReadEntry(
                    parser_mediator, file_object, file_offset, entry_map
                )
            except errors.ParseError:
                # A single corrupt fixed-size record should not abort parsing of
                # the remaining records. Skip it and continue if a full record
                # could still follow; otherwise treat the remainder as trailing
                # data.
                if file_size - file_offset < entry_size:
                    break

                parser_mediator.ProduceExtractionWarning(
                    f"Unable to parse utmp entry at offset: 0x{file_offset:08x}, "
                    f"skipping record"
                )
                file_offset += entry_size
                file_object.seek(file_offset)
                continue

            parser_mediator.ProduceEventData(event_data)

            for warning_string in warning_strings:
                parser_mediator.ProduceExtractionWarning(warning_string)

            file_offset = file_object.tell()


manager.ParsersManager.RegisterParser(UtmpParser)
