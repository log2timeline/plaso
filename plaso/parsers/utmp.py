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
      login_type (int): login type.
      offset (int): offset of the utmp record relative to the start of the file,
          from which the event data was extracted.
      pid (int): process identifier (PID).
      terminal_identifier (int): inittab identifier.
      terminal (str): type of terminal.
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
        self.login_type = None
        self.offset = None
        self.pid = None
        self.terminal_identifier = None
        self.terminal = None
        self.username = None
        self.written_time = None


class UtmpParser(interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
    """Parser for Linux libc6 utmp files."""

    NAME = "utmp"
    DATA_FORMAT = "Linux libc6 utmp file"

    _DEFINITION_FILE = os.path.join(os.path.dirname(__file__), "utmp.yaml")

    _EMPTY_IP_ADDRESS = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    _SUPPORTED_TYPES = frozenset(range(0, 10))

    # A libc6 utmp record is a fixed-size structure. It is 384 bytes on 32-bit
    # platforms and on 64-bit platforms with 32-bit time compatibility (e.g.
    # x86-64), and 400 bytes on 64-bit platforms without it (e.g. aarch64),
    # where the session and timeval fields are 64-bit.
    _ENTRY_SIZE_32BIT = 384
    _ENTRY_SIZE_64BIT = 400

    # The maximum number of records read to determine the record layout and
    # whether a file is a utmp file at all.
    _MAXIMUM_VALIDATION_RECORDS = 16

    # The minimum number of valid non-empty records required to accept a file.
    _MINIMUM_VALIDATION_RECORDS = 2

    # The largest ut_type value used when validating a record. ACCOUNTING (9)
    # is defined but not written in practice.
    _MAXIMUM_VALIDATION_TYPE = 8

    def _ReadEntry(self, parser_mediator, file_object, file_offset, entry_map):
        """Reads an utmp entry.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): a file-like object.
          file_offset (int): offset of the data relative to the start of
              the file-like object.
          entry_map (dtfabric.DataTypeMap): data type map of the utmp record.

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
                f"Unable to parse utmp entry at offset: 0x{file_offset:08x} with "
                f"error: {exception!s}."
            )

        if entry.login_type not in self._SUPPORTED_TYPES:
            raise errors.ParseError(f"Unsupported login type: {entry.login_type:d}")

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
        event_data.login_type = entry.login_type
        event_data.offset = file_offset
        event_data.pid = entry.pid
        event_data.terminal = terminal or None
        event_data.terminal_identifier = entry.terminal_identifier
        event_data.username = username or None
        event_data.written_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=timestamp
        )
        return event_data, warning_strings

    def _IsValidEntry(self, entry):
        """Checks whether an utmp entry satisfies the record invariants.

        Used to determine the record layout and whether a file is a utmp file.
        A record read with the wrong record size, or from a file that is not a
        utmp file, will typically violate one of these invariants.

        Args:
          entry (linux_libc6_utmp_entry): utmp record.

        Returns:
          bool: True if the record is a plausible utmp record.
        """
        if entry.login_type < 0 or entry.login_type > self._MAXIMUM_VALIDATION_TYPE:
            return False

        if (
            entry.microseconds < 0
            or entry.microseconds >= definitions.MICROSECONDS_PER_SECOND
        ):
            return False

        # A non-empty record is expected to identify a terminal.
        if (
            entry.login_type != 0
            and not entry.terminal_identifier
            and not entry.terminal.split(b"\x00")[0]
        ):
            return False

        return True

    def _CountValidEntries(self, file_object, entry_map, entry_size, file_size):
        """Counts valid non-empty records at the start of a file for a layout.

        Empty records are all zeros and remain valid under either record layout,
        so only non-empty records are counted to tell the layouts apart.

        Args:
          file_object (dfvfs.FileIO): a file-like object.
          entry_map (dtfabric.DataTypeMap): utmp record data type map.
          entry_size (int): size of an utmp record for the layout.
          file_size (int): size of the file-like object.

        Returns:
          int: number of valid non-empty records among the first records.
        """
        number_of_entries = min(
            self._MAXIMUM_VALIDATION_RECORDS, file_size // entry_size
        )

        count = 0
        for entry_index in range(number_of_entries):
            file_offset = entry_index * entry_size
            try:
                entry, _ = self._ReadStructureFromFileObject(
                    file_object, file_offset, entry_map
                )
            except (ValueError, errors.ParseError):
                continue

            if entry.login_type != 0 and self._IsValidEntry(entry):
                count += 1

        return count

    def _GetEntryFormat(self, file_object, file_size):
        """Determines the record layout of a utmp file.

        The 32-bit (384-byte) and 64-bit (400-byte) record layouts are told
        apart by reading the first records with each: a record read with the
        wrong record size misaligns and violates the record invariants. A layout
        is only considered when its first record is valid, and the layout with
        the most valid non-empty records is selected. A file is only accepted
        when enough valid non-empty records are found, so the parser does not
        claim files, such as executables, that are not utmp files.

        Args:
          file_object (dfvfs.FileIO): a file-like object.
          file_size (int): size of the file-like object.

        Returns:
          tuple[int, dtfabric.DataTypeMap]: record size and data type map, or
              (None, None) if the file is not a utmp file.
        """
        best_entry_size = None
        best_entry_map = None
        best_count = 0

        for entry_size, definition_name in (
            (self._ENTRY_SIZE_32BIT, "linux_libc6_utmp_entry"),
            (self._ENTRY_SIZE_64BIT, "linux_libc6_utmp_entry_64bit"),
        ):
            if file_size < entry_size:
                continue

            entry_map = self._GetDataTypeMap(definition_name)

            # The first record must itself be a valid utmp record. Files that
            # are not utmp files, such as executables, typically start with data
            # that is not, which keeps the parser from claiming them.
            try:
                first_entry, _ = self._ReadStructureFromFileObject(
                    file_object, 0, entry_map
                )
            except (ValueError, errors.ParseError):
                continue

            if not self._IsValidEntry(first_entry):
                continue

            count = self._CountValidEntries(
                file_object, entry_map, entry_size, file_size
            )
            if count > best_count:
                best_count = count
                best_entry_size = entry_size
                best_entry_map = entry_map

        if best_count < self._MINIMUM_VALIDATION_RECORDS:
            return None, None

        return best_entry_size, best_entry_map

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
        if entry_size is None or entry_map is None:
            raise errors.WrongParser(
                "Unable to determine utmp record layout, not a utmp file"
            )

        file_offset = 0

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
