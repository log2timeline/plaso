"""JSON-L parser plugin for MongoDB log files.

MongoDB 4.4 and later write structured log messages in JSON format.

Also see:
  https://www.mongodb.com/docs/manual/reference/log-messages/
"""

import json

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import jsonl_parser
from plaso.parsers.jsonl_plugins import interface


class MongoDBLogEventData(events.EventData):
    """MongoDB log event data.

    Attributes:
      attributes (list[str]): additional attributes of the log message, formatted
          as "name: value".
      component (str): functional component of the log message, such as
          "NETWORK".
      context (str): name of the thread that caused the log message.
      message_body (str): message body.
      message_identifier (int): identifier of the log message.
      recorded_time (dfdatetime.DateTimeValues): date and time the log entry
          was recorded.
      severity (str): severity of the log message, such as "I" for
          informational.
    """

    DATA_TYPE = "mongodb:log:entry"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.attributes = None
        self.component = None
        self.context = None
        self.message_body = None
        self.message_identifier = None
        self.recorded_time = None
        self.severity = None


class MongoDBLogJSONLPlugin(interface.JSONLPlugin):
    """JSON-L parser plugin for MongoDB log files."""

    NAME = "mongodb_log"
    DATA_FORMAT = "MongoDB log file"

    def _GetDateTimeString(self, json_dict):
        """Retrieves the date and time string of a log message.

        Args:
          json_dict (dict): JSON dictionary of the log record.

        Returns:
          str: ISO 8601 date and time string or None if not available.
        """
        time_value = json_dict.get("t")
        if not isinstance(time_value, dict):
            return None

        date_time_string = time_value.get("$date")
        if not isinstance(date_time_string, str):
            return None

        return date_time_string

    def _ParseRecord(self, parser_mediator, json_dict):
        """Parses a MongoDB log record.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          json_dict (dict): JSON dictionary of the log record.
        """
        attributes = self._GetJSONValue(json_dict, "attr", default_value={})
        if not isinstance(attributes, dict):
            attributes = {}

        attribute_strings = []
        for name, value in attributes.items():
            if not isinstance(value, str):
                value = json.dumps(value, separators=(",", ":"))
            attribute_strings.append(f"{name:s}: {value:s}")

        date_time = None
        corrupted = False

        # The date and time is stored as: "t": {"$date": "2020-05-01T15:16:17.180Z"}
        if self._GetDateTimeString(json_dict):
            date_time, corrupted = self._ParseISO8601DateTimeString(
                parser_mediator, json_dict["t"], "$date"
            )

        event_data = MongoDBLogEventData()
        event_data.attributes = attribute_strings or None
        event_data.component = self._GetJSONValue(json_dict, "c")
        event_data.context = self._GetJSONValue(json_dict, "ctx")
        event_data.message_body = self._GetJSONValue(json_dict, "msg")
        event_data.message_identifier = self._GetJSONValue(json_dict, "id")
        event_data.recorded_time = date_time
        event_data.severity = self._GetJSONValue(json_dict, "s")

        parser_mediator.ProduceEventData(event_data, corrupted=corrupted)

    def CheckRequiredFormat(self, json_dict):
        """Check if the log record has the minimal structure required by the plugin.

        Args:
          json_dict (dict): JSON dictionary of the log record.

        Returns:
          bool: True if this is the correct parser, False otherwise.
        """
        date_time_string = self._GetDateTimeString(json_dict)
        component = json_dict.get("c")
        message_identifier = json_dict.get("id")
        message_body = json_dict.get("msg")
        severity = json_dict.get("s")

        if not date_time_string or not isinstance(message_identifier, int):
            return False

        if not isinstance(component, str) or not isinstance(severity, str):
            return False

        if not isinstance(message_body, str):
            return False

        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()

        try:
            date_time.CopyFromStringISO8601(date_time_string)
        except ValueError:
            return False

        return True


jsonl_parser.JSONLParser.RegisterPlugin(MongoDBLogJSONLPlugin)
