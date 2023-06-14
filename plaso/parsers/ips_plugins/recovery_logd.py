# -*- coding: utf-8 -*-
"""IPS file parser plugin for Apple crash recovery report."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import ips_parser
from plaso.parsers.ips_plugins import interface


class AppleRecoveryLogdEvent(events.EventData):
  """Apple crash recovery event data.

  Attributes:
    application_name (str): name of the application.
    application_version (str): version of the application.
    bug_type (str): type of bug.
    device_model (str): model of the device.
    event_time (dfdatetime.DateTimeValues): date and time of the crash report.
    incident_identifier (str): uuid for crash.
    os_version (str): version of the operating system.
  """
  DATA_TYPE = 'apple:ips_recovery_logd'

  def __init__(self):
    """Initializes event data."""
    super(AppleRecoveryLogdEvent, self).__init__(data_type=self.DATA_TYPE)
    self.application_name = None
    self.application_version = None
    self.bug_type = None
    self.device_model = None
    self.event_time = None
    self.incident_identifier = None
    self.os_version = None


class AppleRecoveryLogdIPSPlugin(interface.IPSPlugin):
  """Parses Apple Crash logs from IPS file."""

  NAME = 'apple_crash_log'
  DATA_FORMAT = 'IPS application crash log'

  ENCODING = 'utf-8'

  REQUIRED_HEADER_KEYS = [
      'app_name', 'app_version', 'bug_type', 'incident_id', 'os_version',
      'timestamp']
  REQUIRED_CONTENT_KEYS = [
      'pid', 'procLaunch', 'threads', 'usedImages']

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  TIMESTAMP_GRAMMAR = (
      _FOUR_DIGITS.setResultsName('year') + pyparsing.Suppress('-') +
      _TWO_DIGITS.setResultsName('month') + pyparsing.Suppress('-') +
      _TWO_DIGITS.setResultsName('day') +
      _TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('seconds') + pyparsing.Suppress('.') +
      _TWO_DIGITS.setResultsName('hundredth') +
      pyparsing.Word(
          pyparsing.nums + '+' + '-').setResultsName('timezone_delta'))

  def __init__(self):
    """Initializes a text parser plugin."""
    super(AppleRecoveryLogdIPSPlugin, self).__init__()
    self._event_data = None

  # pylint: disable=unused-argument
  def Process(self, parser_mediator, ips_file=None, **unused_kwargs):
    """Extracts information from an IPS log file.
    This is the main method that an IPS plugin needs to implement.
    Args:
      parser_mediator (ParserMediator): parser mediator.
      ips_file (Optional[IpsFile]): database.
    Raises:
      ValueError: If the file value is missing.
    """
    if ips_file is None:
      raise ValueError('Missing ips_file value')

    # This will raise if unhandled keyword arguments are passed.
    super(AppleRecoveryLogdIPSPlugin, self).Process(parser_mediator)

    event_data = AppleRecoveryLogdEvent()
    event_data.application_name = ips_file.header.get('app_name')
    event_data.application_version = ips_file.header.get('app_version')
    event_data.bug_type = ips_file.header.get('bug_type')
    event_data.device_model = ips_file.content.get('modelCode')
    event_data.incident_identifier = ips_file.header.get('incident_id')
    event_data.os_version = ips_file.header.get('os_version')

    timestamp = ips_file.header.get('timestamp')

    parsed_timestamp = self.TIMESTAMP_GRAMMAR.parseString(timestamp)

    # dfDateTime takes the time zone offset as number of minutes relative from
    # UTC. So for Easter Standard Time (EST), which is UTC-5:00 the sign needs
    # to be converted, to +300 minutes.
    try:
      time_delta_hours = int(parsed_timestamp['timezone_delta'][:3], 10)
      time_delta_minutes = int(parsed_timestamp['timezone_delta'][3:], 10)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning(
          'unsupported timezone offset value')
      return

    time_zone_offset = (time_delta_hours * -60) + time_delta_minutes

    try:
      event_data.event_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=(
              parsed_timestamp['year'], parsed_timestamp['month'],
              parsed_timestamp['day'], parsed_timestamp['hours'],
              parsed_timestamp['minutes'], parsed_timestamp['seconds']),
          time_zone_offset=time_zone_offset)

    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('unsupported date time value')
      return

    parser_mediator.ProduceEventData(event_data)


ips_parser.IPSParser.RegisterPlugin(AppleRecoveryLogdIPSPlugin)
