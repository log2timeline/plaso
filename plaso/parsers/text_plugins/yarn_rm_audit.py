"""Text parser plugin for Apache Hadoop YARN ResourceManager audit log files.

The ResourceManager audit log (rm-audit.log) is written by the RMAuditLogger
when the RMAUDIT log4j appender is enabled. A log line consists of a date and
time, a log level, the logger name and tab-separated key and value pairs.

Also see:
  https://github.com/apache/hadoop/blob/9d50c6884666e794e45102260a4017bb31802e1b/hadoop-yarn-project/hadoop-yarn/hadoop-yarn-server/hadoop-yarn-server-resourcemanager/src/main/java/org/apache/hadoop/yarn/server/resourcemanager/RMAuditLogger.java
  https://github.com/apache/hadoop/blob/9d50c6884666e794e45102260a4017bb31802e1b/hadoop-common-project/hadoop-common/src/main/conf/log4j.properties
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class YARNResourceManagerAuditLogEventData(events.EventData):
    """YARN ResourceManager audit log event data.

    Attributes:
      application_identifier (str): application identifier (APPID).
      attempt_identifier (str): application attempt identifier (APPATTEMPTID).
      caller_context (str): caller context (CALLERCONTEXT).
      caller_signature (str): caller signature (CALLERSIGNATURE).
      container_identifier (str): container identifier (CONTAINERID).
      description (str): description of the failure (DESCRIPTION).
      include_applications (str): value of the include applications argument
          of a queue information request (INCLUDEAPPS).
      include_child_queues (str): value of the include child queues argument
          of a queue information request (INCLUDECHILDQUEUES).
      ip_address (str): IP address of the client (IP).
      node_label (str): node label (NODELABEL).
      operation (str): operation (OPERATION).
      permissions (str): permissions that were checked (PERMISSIONS).
      queue (str): name of the queue (QUEUENAME).
      recursive (str): value of the recursive argument of a queue information
          request (RECURSIVE).
      resource (str): resource that was allocated or released (RESOURCE).
      result (str): result of the operation, such as "SUCCESS" or "FAILURE"
          (RESULT).
      target (str): target of the operation, such as "ClientRMService"
          (TARGET).
      user (str): name of the user (USER).
      written_time (dfdatetime.DateTimeValues): date and time the log entry
          was written.
    """

    DATA_TYPE = "hadoop:yarn:resourcemanager:audit"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.application_identifier = None
        self.attempt_identifier = None
        self.caller_context = None
        self.caller_signature = None
        self.container_identifier = None
        self.description = None
        self.include_applications = None
        self.include_child_queues = None
        self.ip_address = None
        self.node_label = None
        self.operation = None
        self.permissions = None
        self.queue = None
        self.recursive = None
        self.resource = None
        self.result = None
        self.target = None
        self.user = None
        self.written_time = None


class YARNResourceManagerAuditLogTextPlugin(interface.TextPlugin):
    """Text parser plugin for Apache Hadoop YARN ResourceManager audit logs."""

    NAME = "yarn_rm_audit"
    DATA_FORMAT = "Apache Hadoop YARN ResourceManager audit log (rm-audit.log) file"

    ENCODING = "utf-8"

    # Mapping of the audit log keys to event data attribute names.
    _KEY_ATTRIBUTE_NAMES = {
        "APPATTEMPTID": "attempt_identifier",
        "APPID": "application_identifier",
        "CALLERCONTEXT": "caller_context",
        "CALLERSIGNATURE": "caller_signature",
        "CONTAINERID": "container_identifier",
        "DESCRIPTION": "description",
        "INCLUDEAPPS": "include_applications",
        "INCLUDECHILDQUEUES": "include_child_queues",
        "IP": "ip_address",
        "NODELABEL": "node_label",
        "OPERATION": "operation",
        "PERMISSIONS": "permissions",
        "QUEUENAME": "queue",
        "RECURSIVE": "recursive",
        "RESOURCE": "resource",
        "RESULT": "result",
        "TARGET": "target",
        "USER": "user",
    }

    _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    # Date and time values are formatted as: 2026-11-26 11:15:43,731
    _DATE_TIME = pyparsing.Group(
        _FOUR_DIGITS
        + pyparsing.Suppress("-")
        + _TWO_DIGITS
        + pyparsing.Suppress("-")
        + _TWO_DIGITS
        + _TWO_DIGITS
        + pyparsing.Suppress(":")
        + _TWO_DIGITS
        + pyparsing.Suppress(":")
        + _TWO_DIGITS
        + pyparsing.Suppress(",")
        + _THREE_DIGITS
    ).set_results_name("date_time")

    _LOG_LEVEL = pyparsing.one_of(["DEBUG", "ERROR", "FATAL", "INFO", "TRACE", "WARN"])

    # The logger name is formatted with the log4j %c{2} conversion pattern.
    _LOGGER_NAME = pyparsing.Suppress(
        pyparsing.Literal("resourcemanager.RMAuditLogger:")
    )

    # The key and value pairs are separated by tab characters and always start
    # with the user.
    _KEY_VALUE_PAIRS = pyparsing.Combine(
        pyparsing.Literal("USER=") + pyparsing.rest_of_line()
    ).set_results_name("key_value_pairs")

    _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

    _LOG_LINE = _DATE_TIME + _LOG_LEVEL + _LOGGER_NAME + _KEY_VALUE_PAIRS + _END_OF_LINE

    _LINE_STRUCTURES = [("log_line", _LOG_LINE)]

    VERIFICATION_GRAMMAR = _LOG_LINE

    def _ParseRecord(self, parser_mediator, key, structure):
        """Parses a pyparsing structure.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          key (str): name of the parsed structure.
          structure (pyparsing.ParseResults): tokens from a parsed log line.

        Raises:
          ParseError: if the structure cannot be parsed.
        """
        time_elements_structure = self._GetValueFromStructure(structure, "date_time")

        key_value_pairs = self._GetStringValueFromStructure(
            structure, "key_value_pairs"
        )

        event_data = YARNResourceManagerAuditLogEventData()

        for key_value_pair in key_value_pairs.split("\t"):
            audit_key, _, value = key_value_pair.partition("=")
            attribute_name = self._KEY_ATTRIBUTE_NAMES.get(audit_key, None)
            if attribute_name:
                setattr(event_data, attribute_name, value or None)
            elif audit_key:
                parser_mediator.ProduceExtractionWarning(
                    f"unsupported audit key: {audit_key:s}"
                )

        event_data.written_time = self._ParseTimeElements(time_elements_structure)

        parser_mediator.ProduceEventData(event_data)

    def _ParseTimeElements(self, time_elements_structure):
        """Parses date and time elements of a log line.

        Args:
          time_elements_structure (pyparsing.ParseResults): date and time elements
              of a log line.

        Returns:
          dfdatetime.TimeElementsInMilliseconds: date and time value.

        Raises:
          ParseError: if a valid date and time value cannot be derived from
              the time elements.
        """
        try:
            date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
                time_elements_tuple=time_elements_structure
            )
            date_time.is_local_time = True

            return date_time

        except (IndexError, TypeError, ValueError) as exception:
            raise errors.ParseError(
                f"Unable to parse time elements with error: {exception!s}"
            )

    def CheckRequiredFormat(self, parser_mediator, text_reader):
        """Check if the log record has the minimal structure required by the plugin.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          text_reader (EncodedTextReader): text reader.

        Returns:
          bool: True if this is the correct plugin, False otherwise.
        """
        try:
            structure = self._VerifyString(text_reader.lines)
        except errors.ParseError:
            return False

        time_elements_structure = self._GetValueFromStructure(structure, "date_time")

        try:
            self._ParseTimeElements(time_elements_structure)
        except errors.ParseError:
            return False

        return True


text_parser.TextLogParser.RegisterPlugin(YARNResourceManagerAuditLogTextPlugin)
