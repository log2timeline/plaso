"""Symantec AV Corporate Edition and Endpoint Protection log file parser."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import dsv_parser
from plaso.parsers import manager


class SymantecEventData(events.EventData):
    """Symantec event data.

    Attributes:
      access (str): access.
      action0 (str): action0.
      action1 (str): action1.
      action1_status (str): action1 status.
      action2 (str): action2.
      action2_status (str): action2 status.
      address (str): address.
      backup_identifier (str): backup identifier.
      category (str): category.
      cleaninfo (str): clean information.
      client_group (str): client group.
      compressed (str): compressed.
      definfo (str): definfo.
      def_sequence_number (str): def sequence number.
      deleteinfo (str): delete information.
      depth (str): depth.
      description (str): description.
      domain_identifier (str): domain identifier (GUID).
      domain_name (str): domain name.
      error_code (str): error code.
      event_code (str): event code.
      event_fields (list[str]): event fields.
      extra (str): extra.
      file_path (str): file path.
      flags (str): flags.
      group_identifier (str): group identifier.
      hostname (str): hostname of computer name.
      identifier (str): identifier (GUID).
      last_written_time (dfdatetime.DateTimeValues): entry last written date and time.
      license_expiration_date (str): license expiration date.
      license_feature_name (str): license feature name.
      license_feature_version (str): license feature version.
      license_fulfillment_identifier (str): license fulfillment identifier.
      license_lifecycle (str): license lifecycle.
      license_seats_delta (str): license seats delta.
      license_seats (str): license seats.
      license_seats_total (str): license seats total.
      license_serial_number (str): license serial number.
      license_start_date (str): license start date.
      logger (str): logger.
      login_domain (str): login domain.
      log_session_identifier (str): log session identifier (GUID).
      mac_address (str): MAC address.
      new_ext (str): new ext.
      ntdomain (str): ntdomain.
      offset (str): offset.
      parent (str): parent.
      quarfwd_status (str): quarfwd status.
      remote_ip_address (str): remote IP address.
      remote_machine (str): remote machine.
      scan_identifier (str): scan identifier.
      snd_status (str): snd status.
      status (str): status.
      still_infected (str): still infected.
      username (str): username.
      vbin_identifier (str): vbin identifier.
      vbin_session_identifier (str): vbin session identifier.
      version (str): version.
      virus_identifier (str): virus identifier.
      virus (str): virus.
      virustype (str): virustype.
    """

    DATA_TYPE = "av:symantec:scanlog"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.access = None
        self.action0 = None
        self.action1 = None
        self.action1_status = None
        self.action2 = None
        self.action2_status = None
        self.address = None
        self.backup_identifier = None
        self.category = None
        self.cleaninfo = None
        self.client_group = None
        self.compressed = None
        self.definfo = None
        self.def_sequence_number = None
        self.deleteinfo = None
        self.depth = None
        self.description = None
        self.domain_identifier = None
        self.domain_name = None
        self.error_code = None
        self.event_code = None
        self.event_fields = None
        self.extra = None
        self.file_path = None
        self.flags = None
        self.group_identifier = None
        self.hostname = None
        self.identifier = None
        self.last_written_time = None
        self.license_expiration_date = None
        self.license_feature_name = None
        self.license_feature_version = None
        self.license_fulfillment_identifier = None
        self.license_lifecycle = None
        self.license_seats_delta = None
        self.license_seats = None
        self.license_seats_total = None
        self.license_serial_number = None
        self.license_start_date = None
        self.logger = None
        self.login_domain = None
        self.log_session_identifier = None
        self.mac_address = None
        self.new_ext = None
        self.ntdomain = None
        self.offset = None
        self.parent = None
        self.quarfwd_status = None
        self.remote_ip_address = None
        self.remote_machine = None
        self.scan_identifier = None
        self.snd_status = None
        self.status = None
        self.still_infected = None
        self.username = None
        self.vbin_identifier = None
        self.vbin_session_identifier = None
        self.version = None
        self.virus_identifier = None
        self.virus = None
        self.virustype = None


class SymantecParser(dsv_parser.DSVParser):
    """Parses Symantec AV Corporate Edition and Endpoint Protection log files."""

    NAME = "symantec_scanlog"
    DATA_FORMAT = "Symantec AV Corporate Edition and Endpoint Protection log file"

    COLUMNS = [
        "timestamp",
        "event_code",
        "category",
        "logger",
        "hostname",
        "username",
        "virus",
        "file_path",
        "action1",
        "action2",
        "action0",
        "virustype",
        "flags",
        "description",
        "scan_identifier",
        "new_ext",
        "group_identifier",
        "event_fields",
        "vbin_identifier",
        "virus_identifier",
        "quarfwd_status",
        "access",
        "snd_status",
        "compressed",
        "depth",
        "still_infected",
        "definfo",
        "def_sequence_number",
        "cleaninfo",
        "deleteinfo",
        "backup_identifier",
        "parent",
        "identifier",
        "client_group",
        "address",
        "domain_name",
        "ntdomain",
        "mac_address",
        "version",
        "remote_machine",
        "remote_ip_address",
        "action1_status",
        "action2_status",
        "license_feature_name",
        "license_feature_version",
        "license_serial_number",
        "license_fulfillment_identifier",
        "license_start_date",
        "license_expiration_date",
        "license_lifecycle",
        "license_seats_total",
        "license_seats",
        "error_code",
        "license_seats_delta",
        "status",
        "domain_identifier",
        "log_session_identifier",
        "vbin_session_identifier",
        "login_domain",
        "extra",
    ]

    def _ParseTimestamp(self, timestamp):
        """Parses a Symantec log timestamp.

        A Symantec log timestamp consist of six hexadecimal octets, that represent:
          First octet: Number of years since 1970
          Second octet: Month, where 0 represents January.
          Third octet: Day of the month
          Fourth octet: Number of hours
          Fifth octet: Number of minutes
          Sixth octet: Number of seconds

        For example, 200A13080122 represents November 19, 2002, 8:01:34 AM.

        Args:
          timestamp (str): hexadecimal encoded date and time values.

        Returns:
          dfdatetime.TimeElements: date and time value.

        Raises:
          ParseError: if a valid date and time value cannot be derived from
              the time elements.
        """
        try:
            year, month, day_of_month, hours, minutes, seconds = (
                int(hexdigit[0] + hexdigit[1], 16)
                for hexdigit in zip(timestamp[::2], timestamp[1::2])
            )
            time_elements_tuple = (
                1970 + year,
                month + 1,
                day_of_month,
                hours,
                minutes,
                seconds,
            )
            date_time = dfdatetime_time_elements.TimeElements(
                time_elements_tuple=time_elements_tuple
            )
            date_time.is_local_time = True

            return date_time

        except (TypeError, ValueError) as exception:
            raise errors.ParseError(
                f"Unable to parse time elements with error: {exception!s}"
            )

    def ParseRow(self, parser_mediator, row_offset, row):
        """Parses a line of the log file and produces events.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          row_offset (int): line number of the row.
          row (dict[str, str]): fields of a single row, as specified in COLUMNS.
        """
        timestamp = self._GetRowValue(row, "timestamp")

        # TODO: remove unused attributes.
        event_data = SymantecEventData()
        event_data.access = self._GetRowValue(row, "access")
        event_data.action0 = self._GetRowValue(row, "action0")
        event_data.action1 = self._GetRowValue(row, "action1")
        event_data.action1_status = self._GetRowValue(row, "action1_status")
        event_data.action2 = self._GetRowValue(row, "action2")
        event_data.action2_status = self._GetRowValue(row, "action2_status")
        event_data.address = self._GetRowValue(row, "address")
        event_data.backup_identifier = self._GetRowValue(row, "backup_identifier")
        event_data.category = self._GetRowValue(row, "category")
        event_data.cleaninfo = self._GetRowValue(row, "cleaninfo")
        event_data.client_group = self._GetRowValue(row, "client_group")
        event_data.compressed = self._GetRowValue(row, "compressed")
        event_data.definfo = self._GetRowValue(row, "definfo")
        event_data.def_sequence_number = self._GetRowValue(row, "def_sequence_number")
        event_data.deleteinfo = self._GetRowValue(row, "deleteinfo")
        event_data.depth = self._GetRowValue(row, "depth")
        event_data.description = self._GetRowValue(row, "description")
        event_data.domain_identifier = self._GetRowValue(row, "domain_identifier")
        event_data.domain_name = self._GetRowValue(row, "domain_name")
        event_data.error_code = self._GetRowValue(row, "error_code")
        event_data.event_code = self._GetRowValue(row, "event_code")
        event_data.event_fields = row["event_fields"].split("\t") or None
        event_data.extra = self._GetRowValue(row, "extra")
        event_data.file_path = self._GetRowValue(row, "file_path")
        event_data.flags = self._GetRowValue(row, "flags")
        event_data.group_identifier = self._GetRowValue(row, "group_identifier")
        event_data.hostname = self._GetRowValue(row, "hostname")
        event_data.identifier = self._GetRowValue(row, "identifier")
        event_data.last_written_time = self._ParseTimestamp(timestamp)
        event_data.license_expiration_date = self._GetRowValue(
            row, "license_expiration_date"
        )
        event_data.license_feature_name = self._GetRowValue(row, "license_feature_name")
        event_data.license_feature_version = self._GetRowValue(
            row, "license_feature_version"
        )
        event_data.license_fulfillment_identifier = self._GetRowValue(
            row, "license_fulfillment_identifier"
        )
        event_data.license_lifecycle = self._GetRowValue(row, "license_lifecycle")
        event_data.license_seats_delta = self._GetRowValue(row, "license_seats_delta")
        event_data.license_seats = self._GetRowValue(row, "license_seats")
        event_data.license_seats_total = self._GetRowValue(row, "license_seats_total")
        event_data.license_serial_number = self._GetRowValue(
            row, "license_serial_number"
        )
        event_data.license_start_date = self._GetRowValue(row, "license_start_date")
        event_data.logger = self._GetRowValue(row, "logger")
        event_data.login_domain = self._GetRowValue(row, "login_domain")
        event_data.log_session_identifier = self._GetRowValue(
            row, "log_session_identifier"
        )
        event_data.mac_address = self._GetRowValue(row, "mac_address")
        event_data.new_ext = self._GetRowValue(row, "new_ext")
        event_data.ntdomain = self._GetRowValue(row, "ntdomain")
        event_data.offset = row_offset
        event_data.parent = self._GetRowValue(row, "parent")
        event_data.quarfwd_status = self._GetRowValue(row, "quarfwd_status")
        event_data.remote_ip_address = self._GetRowValue(row, "remote_ip_address")
        event_data.remote_machine = self._GetRowValue(row, "remote_machine")
        event_data.scan_identifier = self._GetRowValue(row, "scan_identifier")
        event_data.snd_status = self._GetRowValue(row, "snd_status")
        event_data.status = self._GetRowValue(row, "status")
        event_data.still_infected = self._GetRowValue(row, "still_infected")
        event_data.username = self._GetRowValue(row, "username")
        event_data.vbin_identifier = self._GetRowValue(row, "vbin_identifier")
        event_data.vbin_session_identifier = self._GetRowValue(
            row, "vbin_session_identifier"
        )
        event_data.version = self._GetRowValue(row, "version")
        event_data.virus_identifier = self._GetRowValue(row, "virus_identifier")
        event_data.virus = self._GetRowValue(row, "virus")
        event_data.virustype = self._GetRowValue(row, "virustype")

        parser_mediator.ProduceEventData(event_data)

    def VerifyRow(self, parser_mediator, row):
        """Verifies if a line of the file is in the expected format.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          row (dict[str, str]): fields of a single row, as specified in COLUMNS.

        Returns:
          bool: True if this is the correct parser, False otherwise.
        """
        timestamp = self._GetRowValue(row, "timestamp")

        try:
            self._ParseTimestamp(timestamp)
        except errors.ParseError:
            return False

        try:
            event_code = int(row["event_code"], 10)
        except (TypeError, ValueError):
            return False

        if event_code < 1 or event_code > 77:
            return False

        try:
            category = int(row["category"], 10)
        except (TypeError, ValueError):
            return False

        if category < 1 or category > 4:
            return False

        return True


manager.ParsersManager.RegisterParser(SymantecParser)
