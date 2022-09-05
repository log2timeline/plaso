# -*- coding: utf-8 -*-
"""Parser for NIDS alert data in the so-called fast-log format,

Fast.log format is a single line log format as shown below. There exist two
variants:

  Snort3:
    Month/Day-Hour:Minute:Second:FractionOfSeconds [**] [sid] "string" [**] \
    [Classification: string] [Priority : int] {protocol} SOURCE_IP:SOURCE_PORT \
    -> DESTINATION_IP:DESTINATION_PORT

  Suricata:
    Year/Month/Day-Hour:Minute:Second:FractionOfSeconds [**] [sid] string [**] \
    [Classification: string] [Priority : int] {protocol} SOURCE_IP:SOURCE_PORT \
    -> DESTINATION_IP:DESTINATION_PORT

More information on the format specification of Suricata can be found here:
  https://suricata.readthedocs.io/en/suricata-6.0.0/configuration/suricata-yaml.html#line-based-alerts-log-fast-log

"""

import re

import pyparsing
from dfdatetime import time_elements as dfdatetime_time_elements
from plaso.containers import events, time_events
from plaso.lib import definitions, errors
from plaso.parsers import manager
from plaso.parsers import text_parser as tp


class NIDSFastAlertEventData(events.EventData):
  """Fast log event data.

  Attributes:
    sid (str): identifier of the rule that triggered the alert,
    message (str): message associated with the alert,
    priority (int): optional integer ranging from 1 (high) to 4 (very low),
    classification (str): optional classification of the alert,
    source_ip (str): source IPv4- or IPv6-address,
    source_port (int): optional source port number,
    destination_ip (str): destination IPv4- or IPv6-address,
    destination_port (int): optional destination port number,
  """

  DATA_TYPE = "nids:alert:fast"

  def __init__(self):
    """Initializes event data."""
    super(NIDSFastAlertEventData, self).__init__(data_type=self.DATA_TYPE)
    self.rule_id = None
    self.message = None
    self.priority = None
    self.classification = None
    self.protocol = None
    self.source_ip = None
    self.source_port = None
    self.destination_ip = None
    self.destination_port = None


class NIDSFastParser(tp.PyparsingSingleLineTextParser):
  """NIDS alert data parser for fast format (alert_fast.txt and fast.log)."""

  NAME = "nids:alert:fast"
  DATA_FORMAT = "NIDS fast alert log"

  _FASTLOG_VERIFICATION_PATTERN = (
      r"^(\d{2}\/)?\d{2}\/\d{2}\-\d{2}:\d{2}:\d{2}.\d{6}\s*\[\*\*\]\s*\[\d*:\d"
      r"*:\d*\]\s*\"?.*\"?\s*\[\*\*\]\s*(\[Classification:\s.*\])?\s*(\[Priori"
      r"ty\:\s*\d{1}\])?\s*\{\w+\}\s((([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}"
      r"|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|("
      r"[0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,"
      r"4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4})"
      r"{1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4"
      r"}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9"
      r"a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-"
      r"5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]).){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9])"
      r"{0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,"
      r"1}[0-9]).){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))|(25[0-5]|2[0-"
      r"4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25"
      r"[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0"
      r"-9]?))(:\d*)?\s*\-\>\s*((([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-"
      r"9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a"
      r"-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:["
      r"0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}"
      r"|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:"
      r"[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-"
      r"F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2"
      r"[0-4]|1{0,1}[0-9]){0,1}[0-9]).){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}"
      r"[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-"
      r"9]).){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))|(25[0-5]|2[0-4][0-"
      r"9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]"
      r"|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
      r")(:\d*)?$"
  )
  _VERIFICATION_REGEX = re.compile(_FASTLOG_VERIFICATION_PATTERN)

  _PYPARSING_COMPONENTS = {
      "year": tp.PyparsingConstants.TWO_DIGITS.setResultsName("year"),
      "month": tp.PyparsingConstants.TWO_DIGITS.setResultsName("month"),
      "day": tp.PyparsingConstants.TWO_DIGITS.setResultsName("day"),
      "hour": tp.PyparsingConstants.TWO_DIGITS.setResultsName("hour"),
      "minute": tp.PyparsingConstants.TWO_DIGITS.setResultsName("minute"),
      "second": tp.PyparsingConstants.TWO_DIGITS.setResultsName("second"),
      "fractional_seconds": pyparsing.Word(pyparsing.nums).setResultsName(
          "fractional_seconds"
      ),
      "sid": pyparsing.Combine(
          tp.PyparsingConstants.INTEGER
          + ":"
          + tp.PyparsingConstants.INTEGER
          + ":"
          + tp.PyparsingConstants.INTEGER
      ).setResultsName("sid"),
      "message": pyparsing.Combine(
          pyparsing.OneOrMore(
              pyparsing.Word(pyparsing.printables, exclude_chars='["')
              | pyparsing.White(" ", max=2)
          )
      ).set_results_name("message"),
      "cls": pyparsing.Regex("[^]]*").setResultsName("cls"),
      "pri": tp.PyparsingConstants.INTEGER.setResultsName("pri"),
      "prot": pyparsing.Word(pyparsing.alphanums).setResultsName("prot"),
      "src_ip": tp.PyparsingConstants.IP_ADDRESS.setResultsName("src_ip"),
      "src_port": tp.PyparsingConstants.INTEGER.setResultsName("src_port"),
      "dst_ip": tp.PyparsingConstants.IP_ADDRESS.setResultsName("dst_ip"),
      "dst_port": tp.PyparsingConstants.INTEGER.setResultsName("dst_port"),
  }
  _PYPARSING_COMPONENTS["md"] = (
      _PYPARSING_COMPONENTS["month"]
      + pyparsing.Suppress("/")
      + _PYPARSING_COMPONENTS["day"]
  )
  _PYPARSING_COMPONENTS["ymd"] = (
      _PYPARSING_COMPONENTS["year"]
      + pyparsing.Suppress("/")
      + _PYPARSING_COMPONENTS["md"]
  )

  _PYPARSING_COMPONENTS["date"] = (
      (_PYPARSING_COMPONENTS["ymd"] | _PYPARSING_COMPONENTS["md"])
      + pyparsing.Suppress(tp.PyparsingConstants.HYPHEN)
      + _PYPARSING_COMPONENTS["hour"]
      + pyparsing.Suppress(":")
      + _PYPARSING_COMPONENTS["minute"]
      + pyparsing.Suppress(":")
      + _PYPARSING_COMPONENTS["second"]
      + pyparsing.Suppress(".")
      + _PYPARSING_COMPONENTS["fractional_seconds"]
  )

  _FASTLOG_LINE = (
      _PYPARSING_COMPONENTS["date"]
      + pyparsing.Suppress("[**] [")
      + _PYPARSING_COMPONENTS["sid"]
      + pyparsing.Suppress("] ")
      + pyparsing.Optional(pyparsing.Suppress('"'))
      + _PYPARSING_COMPONENTS["message"]
      + pyparsing.Optional(pyparsing.Suppress('"'))
      + pyparsing.Suppress("[**]")
      + pyparsing.Optional(
          pyparsing.Suppress(pyparsing.Literal("[Classification:"))
          + _PYPARSING_COMPONENTS["cls"]
          + pyparsing.Suppress("]")
      )
      + pyparsing.Optional(
          pyparsing.Suppress("[Priority:")
          + _PYPARSING_COMPONENTS["pri"]
          + pyparsing.Suppress("]")
      )
      + pyparsing.Suppress("{")
      + _PYPARSING_COMPONENTS["prot"]
      + pyparsing.Suppress("}")
      + _PYPARSING_COMPONENTS["src_ip"]
      + pyparsing.Optional(
          pyparsing.Suppress(":") + _PYPARSING_COMPONENTS["src_port"]
      )
      + pyparsing.Suppress("->")
      + _PYPARSING_COMPONENTS["dst_ip"]
      + pyparsing.Optional(
          pyparsing.Suppress(":") + _PYPARSING_COMPONENTS["dst_port"]
      )
      + pyparsing.Suppress(pyparsing.lineEnd())
  )

  LINE_STRUCTURES = [("nids_fast_alert", _FASTLOG_LINE)]

  def __init__(self):
    """Initializes a parser."""
    super(NIDSFastParser, self).__init__()
    self._last_month = 0
    self._maximum_year = 0
    self._plugin_by_reporter = {}
    self._year_use = 0

  def _UpdateYear(self, mediator, month):
    """Updates the year to use for events, based on last observed month.

    Args:
      mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      month (int): month observed by the parser, where January is 1.
    """
    if not self._year_use:
      self._year_use = mediator.GetEstimatedYear()
    if not self._maximum_year:
      self._maximum_year = mediator.GetLatestYear()

    if not self._last_month:
      self._last_month = month
      return

    if self._last_month == 12 and month == 1:
      self._year_use += 1
    self._last_month = month

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a matching entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.1
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key != "nids_fast_alert":
      raise errors.ParseError(
          "Unable to parse record, unknown structure: {0:s}".format(key)
      )

    month = self._GetValueFromStructure(structure, "month")
    year = self._GetValueFromStructure(structure, "year")

    if month != 0:
      self._UpdateYear(parser_mediator, month)

    year = year + 2000 if year else self._year_use
    day = self._GetValueFromStructure(structure, "day")
    hours = self._GetValueFromStructure(structure, "hour")
    minutes = self._GetValueFromStructure(structure, "minute")
    seconds = self._GetValueFromStructure(structure, "second")

    time_elements_tuple = (year, month, day, hours, minutes, seconds)

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple
      )
      date_time.is_local_time = True
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          "invalid date time value: {0!s}".format(time_elements_tuple)
      )
      return

    event_data = NIDSFastAlertEventData()
    event_data.rule_id = self._GetValueFromStructure(structure, "sid")
    event_data.message = str(
        self._GetValueFromStructure(structure, "message")
    ).strip()
    event_data.priority = self._GetValueFromStructure(structure, "pri")
    event_data.classification = self._GetValueFromStructure(
        structure, "cls"
    )
    event_data.protocol = self._GetValueFromStructure(structure, "prot")
    event_data.source_ip = self._GetValueFromStructure(structure, "src_ip")
    event_data.source_port = self._GetValueFromStructure(
        structure, "src_port"
    )
    event_data.destination_ip = self._GetValueFromStructure(
        structure, "dst_ip"
    )
    event_data.destination_port = self._GetValueFromStructure(
        structure, "dst_port"
    )

    event = time_events.DateTimeValuesEvent(
        date_time,
        definitions.TIME_DESCRIPTION_WRITTEN,
        time_zone=parser_mediator.timezone,
    )
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, parser_mediator, line):
    """Verifies that this is a log file formatted in the fast-syntax
    commonly used by NIDS.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfvfs.
      line (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.

    """
    return bool(self._VERIFICATION_REGEX.match(line))


manager.ParsersManager.RegisterParser(NIDSFastParser)
