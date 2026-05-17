"""Parser for Ivanti Connect Secure (.vc0) log files."""

import ipaddress
import re
import os

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class IvantiVC0EventData(events.EventData):
    """Ivanti Connect Secure (.vc0) log record.

    Attributes:
      body (str): short record text for formatters.
      hostname (str): appliance hostname.
      ip_address (str): IP address found in the record values.
      line_number (str): line number.
      log_type (str): log family, "admin", "access", "diagnostic log", "events",
          "policy trace" or "sensor log".
      message_code (str): Ivanti message code.
      realm (str): Ivanti realm.
      recorded_time (dfdatetime.DateTimeValues): record timestamp.
      record_identifier (str): original record identifier in the format:
          "{timestamp:08x}.{line_number:08x}".
      username (str): username found in the record values.
    """

    DATA_TYPE = "ivanti:connect_secure:vc0:record"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.body = None
        self.hostname = None
        self.ip_address = None
        self.line_number = None
        self.log_type = None
        self.message_code = None
        self.realm = None
        self.recorded_time = None
        self.record_identifier = None
        self.username = None


class VC0FileEntryFilter(interface.BaseFileEntryFilter):
    """File entry filter for Ivanti Connect Secure (.vc0) log files."""

    _FILENAME_RE = re.compile(r"^log\..+?\.vc0(?:\.old)?$", flags=re.IGNORECASE)

    def Match(self, file_entry):
        """Determines if a file entry is an Ivanti .vc0 log file.

        Args:
          file_entry (dfvfs.FileEntry): file entry.

        Returns:
          bool: True if the file entry matches.
        """
        if not file_entry:
            return False

        return bool(self._FILENAME_RE.match(file_entry.name))


class IvantiVC0Parser(interface.FileObjectParser):
    """Parser for Ivanti Connect Secure .vc0 log files."""

    NAME = "ivanti_vc0"
    DATA_FORMAT = "Ivanti Connect Secure (.vc0) log file"

    FILTERS = frozenset([VC0FileEntryFilter()])

    _CHUNK_SIZE = 1024 * 1024
    _HEADER_SIZE = 8192
    _HEADER_SIGNATURE = b"\x05\x00\x00\x00\x01\x00\x00\x00"
    _MAXIMUM_BODY_VALUES = 8

    _LOG_FILENAME_RE = re.compile(r"^log\.(?P<log_type>.+?)\.vc0(?:\.old)?$")
    _MESSAGE_CODE_RE = re.compile(r"^[A-Z]{3}\d{5}$")

    _NON_PRINTABLE_CHARACTER_TRANSLATION_TABLE = (
        definitions.NON_PRINTABLE_CHARACTER_TRANSLATION_TABLE.copy()
    )
    _NON_PRINTABLE_CHARACTER_TRANSLATION_TABLE.pop(ord("\t"), None)

    _RECORD_SEPARATORS_RE = re.compile(b"[\\x00-\\x05\\x0a\\x12\\x13\\x15\\x17]")

    def _CheckHeader(self, file_object, file_size):
        """Checks if the file-like object contains a .vc0 header.

        Args:
          file_object (dfvfs.FileIO): a file-like object.
          file_size (int): file size.

        Returns:
          bool: True if a file-like object contains .vc0 header.
        """
        if file_size < self._HEADER_SIZE:
            return False

        file_object.seek(0, os.SEEK_SET)

        header_data = file_object.read(self._HEADER_SIZE)

        return header_data[0:8] == self._HEADER_SIGNATURE and not any(header_data[8:])

    def _CreateBody(self, record_values, realm, ip_address, username):
        """Builds the short body used by formatters.

        Args:
          record_values (list[str]): values after the realm field.
          realm (str): Ivanti realm.
          ip_address (str): IP address found in the record values.
          username (str): username found in the record values.

        Returns:
          str: body or None if not available.
        """
        body_values = [
            value.strip() for value in record_values if value and value.strip()
        ]
        leading_metadata_values = {
            value for value in (ip_address, realm, username) if value
        }
        while body_values and body_values[0] in leading_metadata_values:
            body_values.pop(0)

        if not body_values:
            return None

        number_of_extra_values = len(body_values) - self._MAXIMUM_BODY_VALUES
        if number_of_extra_values > 0:
            body_values = body_values[: self._MAXIMUM_BODY_VALUES]
            body_values.append(f"... ({number_of_extra_values:d} more fields)")

        return " | ".join(body_values)

    def _GetLogType(self, parser_mediator):
        """Determines the log type from the source filename.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.

        Returns:
          str: log type or None if not available.
        """
        filename = parser_mediator.GetFilename()
        if filename:
            match = self._LOG_FILENAME_RE.match(filename)
            if match:
                return match.group("log_type").lower()

        return None

    def _ExtractIPAddress(self, value):
        """Extracts an IP address from a value.

        Args:
          value (str): field value.

        Returns:
          str: IP address or None if not available.
        """
        try:
            ip_address = ipaddress.ip_address(value.strip())
        except ValueError:
            return None

        return str(ip_address)

    def _ExtractMessageCode(self, fields):
        """Extracts an Ivanti message code from record fields.

        Args:
          fields (list[str]): record fields.

        Returns:
          str: message code or None if not available.
        """
        if len(fields) > 2 and self._MESSAGE_CODE_RE.match(fields[2].strip()):
            return fields[2].strip()

        for field in fields:
            field = field.strip()
            if self._MESSAGE_CODE_RE.match(field):
                return field

        return None

    def _ReadRecords(self, file_object, file_size):
        """Reads .vc0 records.

        Args:
          file_object (dfvfs.FileIO): a file-like object.
          file_size (int): file size.

        Yields:
          tuple: containing:

            bytes: record data.
            int: offset of the record data relative to the start of the file.
        """
        file_data = b""

        record_offset = self._HEADER_SIZE
        file_object.seek(record_offset, os.SEEK_SET)

        while record_offset < file_size:
            data = file_object.read(self._CHUNK_SIZE)
            if not data:
                break

            file_data = b"".join([file_data, data])

            records = self._RECORD_SEPARATORS_RE.split(file_data)
            for record_data in records[:-1]:
                if record_data:
                    yield record_data, record_offset
                record_offset += len(record_data) + 1

            file_data = records[-1]

        if file_data:
            yield file_data, record_offset

    def _ParseRecord(self, parser_mediator, log_type, record_data, record_offset):
        """Parses a .vc0 record.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          log_type (str): log type.
          record_data (bytes): record data.
          record_offset (int): offset of the record data relative to the start of the
              file.
        """
        try:
            record = record_data.decode("utf-8")
        except UnicodeDecodeError:
            parser_mediator.ProduceExtractionWarning(
                f"Invalid record at offset: 0x{record_offset:08x} - unable to decode "
                f"as UTF-8"
            )
            return

        # TODO: determine if this is needed.
        record = record.translate(self._NON_PRINTABLE_CHARACTER_TRANSLATION_TABLE)

        fields = record.split("\t")

        number_of_fields = len(fields)
        if number_of_fields < 3:
            parser_mediator.ProduceExtractionWarning(
                f"Invalid record at offset: 0x{record_offset:08x} - unsupported number "
                f"of fields: {number_of_fields:d}"
            )
            return

        record_identifier = fields[0]
        if "." not in record_identifier:
            parser_mediator.ProduceExtractionWarning(
                f"Invalid record at offset: 0x{record_offset:08x} - record identifier: "
                f"{record_identifier:s} missing '.'"
            )
            return

        timestamp_string, _, line_number_string = record_identifier.partition(".")

        if not timestamp_string:
            parser_mediator.ProduceExtractionWarning(
                f"Invalid record at offset: 0x{record_offset:08x} - record identifier: "
                f"{record_identifier:s} missing timestamp"
            )
            return

        if not line_number_string:
            parser_mediator.ProduceExtractionWarning(
                f"Invalid record at offset: 0x{record_offset:08x} - record identifier: "
                f"{record_identifier:s} missing line number"
            )
            return

        try:
            timestamp = int(timestamp_string, 16)
        except ValueError:
            parser_mediator.ProduceExtractionWarning(
                f"Invalid record at offset: 0x{record_offset:08x} - record identifier: "
                f"{record_identifier:s} unsupported timestamp"
            )
            return

        try:
            line_number = int(line_number_string, 16)
        except ValueError:
            parser_mediator.ProduceExtractionWarning(
                f"Invalid record at offset: 0x{record_offset:08x} - record identifier: "
                f"{record_identifier:s} unsupported line number"
            )
            return

        message_code = self._ExtractMessageCode(fields)
        if not message_code:
            parser_mediator.ProduceExtractionWarning(
                f"Invalid record at offset: 0x{record_offset:08x} - unable to extract "
                f"message code"
            )

        event_data = IvantiVC0EventData()
        event_data.hostname = fields[1] or None
        event_data.line_number = line_number
        event_data.log_type = log_type
        event_data.message_code = message_code
        event_data.recorded_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
        event_data.record_identifier = record_identifier

        if number_of_fields > 4:
            event_data.realm = fields[4] or None
        if number_of_fields > 5:
            event_data.ip_address = self._ExtractIPAddress(fields[5])
        if number_of_fields > 6:
            event_data.username = fields[6] or None

        event_data.body = self._CreateBody(
            fields[5:], event_data.realm, event_data.ip_address, event_data.username
        )
        parser_mediator.ProduceEventData(event_data)

    def ParseFileObject(self, parser_mediator, file_object):
        """Parses an Ivanti Connect Secure (.vc0) log file-like object.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): a file-like object.

        Raises:
          WrongParser: when the file cannot be parsed.
        """
        file_size = file_object.get_size()
        if not self._CheckHeader(file_object, file_size):
            raise errors.WrongParser("Not an Ivanti Connect Secure (.vc0) log file.")

        if file_size > self._HEADER_SIZE:
            log_type = self._GetLogType(parser_mediator)

            for record_data, record_offset in self._ReadRecords(file_object, file_size):
                if parser_mediator.abort:
                    break

                self._ParseRecord(parser_mediator, log_type, record_data, record_offset)


manager.ParsersManager.RegisterParser(IvantiVC0Parser)
