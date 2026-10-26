"""Compound ZIP parser plugin for Apple Wallet pass (pkpass) files."""

import json
import re
import zipfile

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import czip
from plaso.parsers.czip_plugins import interface


class AppleWalletPassEventData(events.EventData):
    """Apple Wallet pass event data.

    Attributes:
      description (str): description of the pass.
      expiration_time (dfdatetime.DateTimeValues): date and time the pass
          expires.
      logo_text (str): text displayed next to the logo of the pass.
      organization_name (str): name of the organization that created and
          signed the pass.
      pass_type_identifier (str): pass type identifier.
      relevant_time (dfdatetime.DateTimeValues): date and time the pass is
          relevant, for example the start time of an event.
      serial_number (str): serial number that uniquely identifies the pass.
      team_identifier (str): team identifier of the organization that created
          and signed the pass.
      voided (bool): True if the pass is void.
    """

    DATA_TYPE = "apple:wallet:pass"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.description = None
        self.expiration_time = None
        self.logo_text = None
        self.organization_name = None
        self.pass_type_identifier = None
        self.relevant_time = None
        self.serial_number = None
        self.team_identifier = None
        self.voided = None


class AppleWalletPassPlugin(interface.CompoundZIPPlugin):
    """Compound ZIP parser plugin for Apple Wallet pass (pkpass) files.

    Also see:
      https://developer.apple.com/documentation/walletpasses/pass
    """

    NAME = "pkpass"
    DATA_FORMAT = "Apple Wallet pass (pkpass) file"

    REQUIRED_PATHS = frozenset(["manifest.json", "pass.json"])

    # Keys that are required in pass.json.
    _REQUIRED_KEYS = frozenset(["formatVersion", "passTypeIdentifier", "serialNumber"])

    # W3C date and time string without seconds, for example:
    # 2011-12-08T13:00-08:00
    _DATE_TIME_WITHOUT_SECONDS_RE = re.compile(
        r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})(Z|[+-]\d{2}:\d{2})$"
    )

    def _GetDateTimeValue(self, parser_mediator, pass_json, name):
        """Retrieves a date and time value from pass.json.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          pass_json (dict[str, object]): contents of pass.json.
          name (str): name of the value.

        Returns:
          dfdatetime.TimeElements: date and time value or None if not available.
        """
        date_time_string = pass_json.get(name)
        if date_time_string is None:
            return None

        if not isinstance(date_time_string, str):
            parser_mediator.ProduceWarning(f"Unsupported date and time value: {name:s}")
            return None

        # Date and time strings are in W3C format, where seconds are optional.
        date_time_string = self._DATE_TIME_WITHOUT_SECONDS_RE.sub(
            r"\1:00\2", date_time_string
        )

        date_time = dfdatetime_time_elements.TimeElements()

        try:
            date_time.CopyFromStringISO8601(date_time_string)
        except ValueError as exception:
            parser_mediator.ProduceWarning(
                f"Unable to parse date and time value: {name:s} with error: "
                f"{exception!s}"
            )
            return None

        return date_time

    def _GetStringValue(self, pass_json, name):
        """Retrieves a string value from pass.json.

        Args:
          pass_json (dict[str, object]): contents of pass.json.
          name (str): name of the value.

        Returns:
          str: string value or None if not available.
        """
        value = pass_json.get(name)
        if not isinstance(value, str):
            return None

        return value

    def _ParseZIPFile(self, parser_mediator, zip_file):
        """Extracts events from an Apple Wallet pass (pkpass) file.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          zip_file (zipfile.ZipFile): the ZIP file. It should not be closed in
              this method, but will be closed by the parser logic in czip.py.
        """
        try:
            pass_json_data = zip_file.read("pass.json")
            pass_json = json.loads(pass_json_data.decode("utf-8"))
        except (
            KeyError,
            OSError,
            RecursionError,
            UnicodeDecodeError,
            ValueError,
            zipfile.BadZipfile,
        ) as exception:
            parser_mediator.ProduceWarning(
                f"Unable to read pass.json with error: {exception!s}"
            )
            return

        if not isinstance(pass_json, dict) or not self._REQUIRED_KEYS.issubset(
            pass_json.keys()
        ):
            parser_mediator.ProduceWarning("Unsupported pass.json, not a pass")
            return

        voided = pass_json.get("voided")

        event_data = AppleWalletPassEventData()
        event_data.description = self._GetStringValue(pass_json, "description")
        event_data.expiration_time = self._GetDateTimeValue(
            parser_mediator, pass_json, "expirationDate"
        )
        event_data.logo_text = self._GetStringValue(pass_json, "logoText")
        event_data.organization_name = self._GetStringValue(
            pass_json, "organizationName"
        )
        event_data.pass_type_identifier = self._GetStringValue(
            pass_json, "passTypeIdentifier"
        )
        event_data.relevant_time = self._GetDateTimeValue(
            parser_mediator, pass_json, "relevantDate"
        )
        event_data.serial_number = self._GetStringValue(pass_json, "serialNumber")
        event_data.team_identifier = self._GetStringValue(pass_json, "teamIdentifier")
        event_data.voided = voided if isinstance(voided, bool) else None

        parser_mediator.ProduceEventData(event_data)


czip.CompoundZIPParser.RegisterPlugin(AppleWalletPassPlugin)
